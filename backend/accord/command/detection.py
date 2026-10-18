"""Restart-safe internal detection of committed server persona events.

Per-event sliding windows use event time and the cold-store snapshot at evaluation.
Findings are observations, not approval, enforcement or external notifications.
"""

import hashlib
import json
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime, timedelta

from sqlalchemy import exists, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.detection_events import batch_event
from accord.command.detection_models import DetectionReceipt
from accord.command.models import Event
from accord.command.rules import DEFAULT_RULES, Rule
from accord.config import get_settings
from accord.telemetry.registry import NON_ROUTE_ACTIONS

PERSONA_ACTIONS = frozenset(action for action in NON_ROUTE_ACTIONS if action.startswith("persona."))
SEVERITIES = {"debug": 0, "info": 1, "warn": 2, "error": 3, "critical": 4}
BATCH_SIZE = 100
MAX_WINDOW_SECONDS = max(rule.window_seconds for rule in DEFAULT_RULES)


def rules_digest() -> str:
    encoded = json.dumps(
        {"engine": "persona-event-window-v1", "rules": [asdict(rule) for rule in DEFAULT_RULES]},
        sort_keys=True,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def matches(rule: Rule, event: Event) -> bool:
    """Apply every catalogue predicate; unknown severity never escalates a finding."""
    return (
        (not rule.actions or event.action in rule.actions)
        and (bool(rule.actions) or event.action not in rule.exclude_actions)
        and (not rule.outcomes or event.outcome in rule.outcomes)
        and (
            rule.min_severity is None
            or SEVERITIES.get(event.severity, -1) >= SEVERITIES[rule.min_severity]
        )
    )


async def count_window(session: AsyncSession, rule: Rule, event: Event) -> int:
    """Only this tenant's trusted persona observations may contribute to its findings."""
    query = select(func.count(Event.event_id)).where(
        Event.tenant_id == event.tenant_id,
        Event.source == "server",
        Event.category == "persona",
        Event.action.in_(PERSONA_ACTIONS),
        Event.ts > event.ts - timedelta(seconds=rule.window_seconds),
        Event.ts <= event.ts,
    )
    if rule.actions:
        query = query.where(Event.action.in_(rule.actions))
    elif rule.exclude_actions:
        query = query.where(Event.action.not_in(rule.exclude_actions))
    if rule.outcomes:
        query = query.where(Event.outcome.in_(rule.outcomes))
    if rule.min_severity:
        allowed = [key for key, rank in SEVERITIES.items() if rank >= SEVERITIES[rule.min_severity]]
        query = query.where(Event.severity.in_(allowed))
    return int(await session.scalar(query) or 0)


async def evaluate_event(session: AsyncSession, event: Event, digest: str) -> DetectionReceipt:
    if event.tenant_id is None:
        raise RuntimeError("detection event missing workspace")
    findings = []
    for rule in DEFAULT_RULES:
        if matches(rule, event):
            count = await count_window(session, rule, event)
            if count >= rule.threshold:
                findings.append({"rule_id": rule.id, "count": count, "severity": rule.severity})
    return DetectionReceipt(
        event_id=event.event_id,
        workspace_id=event.tenant_id,
        evaluated_at=datetime.now(UTC),
        rules_digest=digest,
        window_within_retention=(
            event.ts - timedelta(seconds=MAX_WINDOW_SECONDS)
            >= datetime.now(UTC) - timedelta(days=get_settings().command_retention_days)
        ),
        findings=findings,
    )


async def evaluate_once(session: AsyncSession) -> int:
    """Commit findings/checkpoints together; any fault rolls the batch back for retry.

    Transaction advisory lock serializes workers and retention. There is no timestamp
    cursor: late events remain discoverable. Cancellation/process loss releases the lock.
    """
    async with session.begin():
        await session.execute(text("SELECT pg_advisory_xact_lock(9182402)"))
        done = exists().where(DetectionReceipt.event_id == Event.event_id)
        events = await session.scalars(
            select(Event)
            .where(
                Event.tenant_id.is_not(None),
                Event.source == "server",
                Event.category == "persona",
                Event.action.in_(PERSONA_ACTIONS),
                ~done,
            )
            .order_by(Event.ts, Event.event_id)
            .limit(BATCH_SIZE)
        )
        rows = list(events)
        digest = rules_digest()
        for event in rows:
            session.add(await evaluate_event(session, event, digest))
        for workspace, count in Counter(event.tenant_id for event in rows).items():
            if workspace is not None:
                session.add(batch_event(workspace, count, digest))
    return len(rows)
