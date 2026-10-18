"""Drain the telemetry Redis Stream into the Postgres ``events`` cold store.

Idempotent by ``event_id`` (re-delivery after a restart inserts nothing new). A cursor in Redis
tracks progress. Poison-pill (unparseable) entries are skipped, never fatal.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from redis.asyncio import Redis
from sqlalchemy import and_, delete, exists, func, or_, select, text, true
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.audit import AUDITABLE_ACTIONS
from accord.command.detection import MAX_WINDOW_SECONDS, PERSONA_ACTIONS
from accord.command.detection_models import DetectionReceipt
from accord.command.models import AuditLog, Event
from accord.config import get_settings
from accord.telemetry.envelope import SOURCE_SERVER


def _uuid_or_none(value: Any) -> uuid.UUID | None:
    if not value:
        return None
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError):
        return None


def _to_row(ev: dict[str, Any]) -> dict[str, Any]:
    actor = ev.get("actor") or {}
    resource = ev.get("resource") or {}
    return {
        "event_id": ev["event_id"],
        "ts": datetime.fromisoformat(ev["ts"]),
        "schema_v": ev.get("schema_v", 1),
        "actor_type": actor.get("type", "system"),
        "actor_id": actor.get("id"),
        "sid": actor.get("sid"),
        "tenant_id": _uuid_or_none(ev.get("tenant_id")),
        "category": ev.get("category", ""),
        "action": ev["action"],
        "outcome": ev.get("outcome", ""),
        "severity": ev.get("severity", "info"),
        "resource_type": resource.get("type"),
        "resource_id": resource.get("id"),
        "correlation_id": ev.get("correlation_id"),
        "ip": ev.get("ip"),
        # Only this service writes to the stream, so an ABSENT source is a server-emitted
        # event enqueued before the field existed — backfilling those as server-observed is
        # correct, and the migration backfills stored rows the same way. A PRESENT-but-unknown
        # value is different: it is kept verbatim, so the sealer's source filter excludes it
        # (fail-closed for the chain) instead of `or`-coercing garbage into trusted "server".
        "source": SOURCE_SERVER if ev.get("source") is None else ev["source"],
        "metadata_": ev.get("metadata") or {},
    }


async def consume_once(redis: Redis, session: AsyncSession) -> int:
    """Drain new stream entries into the events table. Returns the number stored."""
    settings = get_settings()
    stream = settings.telemetry_stream
    cursor_key = f"{stream}:cursor"
    last_id: str = str(await redis.get(cursor_key) or "0-0")
    ms, _, seq = last_id.partition("-")
    start = "0-0" if last_id == "0-0" else f"{ms}-{int(seq or 0) + 1}"

    entries = await redis.xrange(stream, min=start, count=500)
    if not entries:
        return 0

    rows: list[dict[str, Any]] = []
    new_cursor: str = last_id
    for entry_id, fields in entries:
        new_cursor = str(entry_id)
        raw = (fields or {}).get("e")
        if not raw:
            continue
        try:
            rows.append(_to_row(json.loads(raw)))
        except (json.JSONDecodeError, TypeError, KeyError, ValueError):
            continue  # poison pill — skip, never fatal

    stored = 0
    if rows:
        ids = [r["event_id"] for r in rows]
        existing = set(
            (await session.execute(select(Event.event_id).where(Event.event_id.in_(ids))))
            .scalars()
            .all()
        )
        fresh = [r for r in rows if r["event_id"] not in existing]
        session.add_all([Event(**r) for r in fresh])
        stored = len(fresh)
        await session.commit()

    await redis.set(cursor_key, new_cursor)
    return stored


async def purge_expired(session: AsyncSession) -> int:
    """Expire cold records, retaining auditable server events until they are sealed."""
    cutoff = datetime.now(UTC) - timedelta(days=get_settings().command_retention_days)
    await session.execute(text("SELECT pg_advisory_xact_lock(9182402)"))
    sealed = exists().where(AuditLog.event_id == Event.event_id)
    evaluated = exists().where(DetectionReceipt.event_id == Event.event_id)
    persona = and_(
        Event.source == SOURCE_SERVER,
        Event.category == "persona",
        Event.action.in_(PERSONA_ACTIONS),
        Event.tenant_id.is_not(None),
    )
    oldest_pending = await session.scalar(select(func.min(Event.ts)).where(persona, ~evaluated))
    support_expired = (
        or_(~persona, Event.ts < oldest_pending - timedelta(seconds=MAX_WINDOW_SECONDS))
        if oldest_pending is not None
        else true()
    )
    expired = (
        delete(Event)
        .where(
            Event.ts < cutoff,
            support_expired,
            or_(Event.action.not_in(AUDITABLE_ACTIONS), Event.source != SOURCE_SERVER, sealed),
            or_(~persona, evaluated),
        )
        .returning(Event.event_id)
        .cte("expired_events")
    )
    count = await session.scalar(select(func.count()).select_from(expired))
    await session.commit()
    return int(count or 0)
