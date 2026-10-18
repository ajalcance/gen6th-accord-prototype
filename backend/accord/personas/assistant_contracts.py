"""Advisory reviewer brief contracts. The model never approves, identifies or decides rights."""

from __future__ import annotations

import re
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

NOTICE = (
    "Advisory draft from an AI model, based only on the text the creator saved. It does not "
    "approve, identify, or decide ownership or permission. An independent human reviewer decides."
)
SUMMARY_MAX, ITEM_MAX, ITEMS_MAX = 450, 160, 4
Summary = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=SUMMARY_MAX)
]
Item = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=ITEM_MAX)]
_UNSAFE = re.compile(r"[\x00-\x1f\x7f<>`]|https?:|www\.", re.IGNORECASE)


def clean(value: str) -> str:
    """Model output is display text only: no markup, control characters or links."""
    if _UNSAFE.search(value):
        raise ValueError("model output contains markup, control characters or a link")
    return value


class BriefQuery(BaseModel):
    """Which saved version to brief on; the server supplies the actor and the content."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    persona_id: UUID
    revision: int | None = Field(default=None, ge=1, strict=True)


class BriefDraft(BaseModel):
    """Validated model output. Anything that does not fit is rejected, never repaired."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    state: Literal["brief", "insufficient_information"]
    summary: Summary
    gaps: list[Item] = Field(max_length=ITEMS_MAX)
    questions: list[Item] = Field(max_length=ITEMS_MAX)

    @field_validator("summary")
    @classmethod
    def summary_is_plain(cls, value: str) -> str:
        return clean(value)

    @field_validator("gaps", "questions")
    @classmethod
    def items_are_plain(cls, values: list[str]) -> list[str]:
        return [clean(v) for v in values]


class ReviewerBrief(BaseModel):
    """Server response: the draft plus where it came from and what it is not."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    persona_id: UUID
    version_id: UUID
    revision: int = Field(ge=1, strict=True)
    state: Literal["brief", "insufficient_information"]
    summary: Summary
    gaps: list[Item] = Field(max_length=ITEMS_MAX)
    questions: list[Item] = Field(max_length=ITEMS_MAX)
    model: str = Field(min_length=1, max_length=200)
    model_revision: str = Field(min_length=1, max_length=160)
    generated_at: AwareDatetime
    notice: str

    @model_validator(mode="after")
    def fixed_notice(self) -> Self:
        if self.notice != NOTICE:
            raise ValueError("the advisory notice is fixed by the server")
        return self
