"""Workspace-only annotations; neither confirmation nor aliases confer rights."""

import json
from typing import Literal, Self
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from accord.personas.contracts import ActorRef, Name


class Credit(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    name: Name
    kind: Literal["human", "organization"]
    role: Literal["design", "writing", "direction", "illustration", "source_performance", "other"]
    actor_ref: ActorRef | None = None
    evidence_id: UUID | None = None

    @model_validator(mode="after")
    def human_account(self) -> Self:
        if self.kind == "organization" and self.actor_ref is not None:
            raise ValueError("organization attestation is not available")
        return self


class CreditContent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    aliases: tuple[Name, ...] = Field(default=(), max_length=8)
    credits: tuple[Credit, ...] = Field(default=(), max_length=12)

    @model_validator(mode="after")
    def unique_entries(self) -> Self:
        names = [value.casefold() for value in self.aliases]
        entries = [credit.model_dump_json() for credit in self.credits]
        if len(set(names)) != len(names) or len(set(entries)) != len(entries):
            raise ValueError("duplicate aliases or credits")
        encoded = json.dumps(
            self.model_dump(mode="json"), ensure_ascii=False, separators=(",", ":")
        )
        if len(encoded.encode()) > 10000:
            raise ValueError("credit content exceeds its metadata byte budget")
        return self


class CreditSubject(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    version_id: UUID


class SaveCredits(CreditSubject):
    request_id: UUID
    expected_previous_id: UUID | None = None
    content: CreditContent


class CreditSnapshot(CreditSubject):
    id: UUID
    workspace_id: UUID
    request_id: UUID
    ordinal: int = Field(ge=1, strict=True)
    declared_by: ActorRef
    recorded_at: AwareDatetime
    content: CreditContent


class ConfirmCredit(CreditSubject):
    request_id: UUID
    profile_id: UUID
    credit_index: int = Field(ge=0, le=11, strict=True)


class CreditConfirmation(ConfirmCredit):
    id: UUID
    workspace_id: UUID
    actor_ref: ActorRef
    recorded_at: AwareDatetime


class CreditProfile(CreditSubject):
    workspace_id: UUID
    snapshot: CreditSnapshot | None
    confirmations: tuple[CreditConfirmation, ...] = Field(default=(), max_length=12)

    @model_validator(mode="after")
    def scoped_receipts(self) -> Self:
        profile = self.snapshot
        if profile is None:
            if self.confirmations:
                raise ValueError("confirmation without a profile")
            return self
        if profile.workspace_id != self.workspace_id or profile.version_id != self.version_id:
            raise ValueError("profile scope mismatch")
        indices: set[int] = set()
        for receipt in self.confirmations:
            if (
                receipt.workspace_id != self.workspace_id
                or receipt.version_id != self.version_id
                or receipt.profile_id != profile.id
                or receipt.credit_index >= len(profile.content.credits)
                or receipt.credit_index in indices
            ):
                raise ValueError("confirmation scope mismatch")
            credit = profile.content.credits[receipt.credit_index]
            if credit.kind != "human" or credit.actor_ref != receipt.actor_ref:
                raise ValueError("confirmation actor mismatch")
            indices.add(receipt.credit_index)
        return self
