"""Synthetic lifecycle declarations; no actual rights or identity are established."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from accord.personas.lifecycle_contracts import (
    AppendLifecycle,
    Assessment,
    Concern,
    Dossier,
    LifecycleReceipt,
    Operator,
    Provenance,
    RequirementStatus,
    Response,
    Right,
)


def dossier(operator: str = "viewer") -> Dossier:
    now = datetime.now(UTC)
    return Dossier(
        kind="dossier",
        operator=Operator(
            name="Operator",
            actor_ref=operator,
            authority="Synthetic studio authorization",
            evidence_id=uuid4(),
        ),
        rights=(
            Right(
                kind="likeness",
                holder="Fictional studio",
                scope="Private rehearsal only",
                withdrawal="Owner may withdraw",
                evidence_id=uuid4(),
                starts_at=now - timedelta(days=1),
                ends_at=now + timedelta(days=30),
            ),
        ),
        provenance=Provenance(
            method="mixed",
            provider="Fixture tool",
            model_version="Fixture 1",
            disclosure="Synthetic test only",
        ),
    )


def command(version: UUID | None = None) -> AppendLifecycle:
    return AppendLifecycle(version_id=version or uuid4(), request_id=uuid4(), content=dossier())


def receipt(
    command: AppendLifecycle,
    workspace: UUID | None = None,
    persona: UUID | None = None,
    actor: str = "creator-a",
) -> LifecycleReceipt:
    return LifecycleReceipt(
        **command.model_dump(),
        id=uuid4(),
        workspace_id=workspace or uuid4(),
        persona_id=persona or uuid4(),
        ordinal=1,
        actor_ref=actor,
        recorded_at=datetime.now(UTC),
        evidence_digests={},
    )


def assessment(profile: UUID, requirement: str = "rights") -> Assessment:
    return Assessment.model_validate(
        {
            "kind": "assessment",
            "profile_id": profile,
            "requirement": requirement,
            "decision": "approved",
            "statement": "Synthetic documentary assessment; no real rights",
            "valid_until": datetime.now(UTC) + timedelta(days=7),
        }
    )


def requirements(profile: UUID) -> tuple[RequirementStatus, ...]:
    return tuple(
        RequirementStatus.model_validate(
            {
                "requirement": dimension,
                "status": "approved",
                "assessment": receipt(
                    command().model_copy(update={"content": assessment(profile, dimension)})
                ).model_dump(),
            }
        )
        for dimension in ("operator", "rights", "content")
    )


def response_command(version: UUID, concern: UUID) -> AppendLifecycle:
    return AppendLifecycle(
        version_id=version,
        request_id=uuid4(),
        content=Response(
            kind="response",
            concern_id=concern,
            decision="suspended",
            statement="Synthetic independent decision",
        ),
    )


def concern_command(version: UUID) -> AppendLifecycle:
    return AppendLifecycle(
        version_id=version,
        request_id=uuid4(),
        content=Concern(
            kind="concern",
            category="rights",
            statement="Synthetic concern",
        ),
    )
