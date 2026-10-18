"""Seal source receipts and bounded findings against immutable row context."""

import hashlib
import json

from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.evidence_crypto import KeyWrapper, SealedEvidence, seal, unseal
from accord.personas.investigation_contracts import InvestigationCommand, InvestigationResult
from accord.personas.investigation_models import InvestigationRecord


def intent_fingerprint(command: InvestigationCommand) -> str:
    return hashlib.sha256(command.model_dump_json().encode()).hexdigest()


def context(row: InvestigationRecord) -> bytes:
    return json.dumps(
        [
            "accord-investigation-v1",
            str(row.workspace_id),
            str(row.id),
            str(row.version_id),
            str(row.portrait_id),
            str(row.request_id),
            row.actor_ref,
            row.ordinal,
            row.fingerprint,
            row.recorded_at.isoformat(),
        ],
        separators=(",", ":"),
    ).encode()


async def load(row: InvestigationRecord, wrapper: KeyWrapper) -> InvestigationResult:
    data = await unseal(
        SealedEvidence(row.ciphertext, row.nonce, row.key_id, row.wrapped_key),
        context(row),
        wrapper,
    )
    if len(data) > 65536:
        raise RuntimeError("investigation storage bound exceeded")
    result = InvestigationResult.model_validate_json(data)
    fields = (
        "id",
        "workspace_id",
        "version_id",
        "portrait_id",
        "request_id",
        "actor_ref",
        "ordinal",
        "recorded_at",
    )
    if any(getattr(result, field) != getattr(row, field) for field in fields):
        raise RuntimeError("investigation context mismatch")
    return result


async def store(
    session: AsyncSession,
    result: InvestigationResult,
    command: InvestigationCommand,
    wrapper: KeyWrapper,
) -> None:
    fields = (
        "id",
        "workspace_id",
        "version_id",
        "portrait_id",
        "request_id",
        "actor_ref",
        "ordinal",
        "recorded_at",
    )
    row = InvestigationRecord(
        **{field: getattr(result, field) for field in fields},
        fingerprint=intent_fingerprint(command),
    )
    data = result.model_dump_json().encode()
    if len(data) > 65536:
        raise RuntimeError("investigation storage bound exceeded")
    sealed = await seal(data, context(row), wrapper)
    row.ciphertext, row.nonce = sealed.ciphertext, sealed.nonce
    row.key_id, row.wrapped_key = sealed.key_id, sealed.wrapped_key
    session.add(row)
