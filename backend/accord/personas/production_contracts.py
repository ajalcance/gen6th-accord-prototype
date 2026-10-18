"""A continuing performer plays a named role; references remain submitted claims."""

from typing import Literal, Self, cast
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    model_serializer,
    model_validator,
)

from accord.personas.contracts import ActorRef, Name, Statement


class SupportingReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["consent", "claim"]
    evidence_id: UUID


class ProductionUse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    title: Name
    episode: Name
    role_name: Name
    adaptation: Statement
    supporting_references: tuple[SupportingReference, ...] = Field(max_length=8)
    governance_profile_id: UUID | None = None
    responsible_operator: ActorRef | None = None
    use_mode: Literal["production", "trial"] = "production"
    distribution: Literal["private", "public"] = "public"
    voice_use: bool = Field(default=False, strict=True)

    @model_serializer(mode="wrap")
    def legacy_shape(self, handler: SerializerFunctionWrapHandler) -> dict[str, object]:
        data = cast(dict[str, object], handler(self))
        if self.governance_profile_id is None:
            for key in (
                "governance_profile_id",
                "responsible_operator",
                "use_mode",
                "distribution",
                "voice_use",
            ):
                data.pop(key, None)
        return data

    @model_validator(mode="after")
    def distinct_references(self) -> Self:
        if self.governance_profile_id is None and (
            self.responsible_operator is not None
            or self.use_mode != "production"
            or self.distribution != "public"
            or self.voice_use
        ):
            raise ValueError("lifecycle scope requires an exact dossier binding")
        if self.governance_profile_id is not None and self.responsible_operator is None:
            raise ValueError("bound use requires its responsible operator")
        if self.use_mode == "trial" and self.distribution != "private":
            raise ValueError("trial distribution must remain private")
        ids = tuple(row.evidence_id for row in self.supporting_references)
        if len(set(ids)) != len(ids):
            raise ValueError("supporting evidence IDs must be distinct")
        return self
