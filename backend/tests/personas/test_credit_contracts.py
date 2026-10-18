"""Credit assertions do not accept a client-built trust marker."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from accord.personas.credit_contracts import (
    ConfirmCredit,
    Credit,
    CreditConfirmation,
    CreditContent,
    CreditProfile,
    CreditSnapshot,
    SaveCredits,
)
from accord.personas.credit_service import require_self_confirmation
from accord.personas.repository import AccessDeniedError
from accord.personas.workflow_contracts import WorkflowActor


def declaration() -> SaveCredits:
    return SaveCredits(
        request_id=uuid4(),
        version_id=uuid4(),
        content=CreditContent(
            aliases=("Nova",),
            credits=(Credit(name="Ari", kind="human", role="design", actor_ref="ari"),),
        ),
    )


def profile() -> CreditSnapshot:
    c = declaration()
    return CreditSnapshot(
        id=uuid4(),
        workspace_id=uuid4(),
        request_id=c.request_id,
        version_id=c.version_id,
        ordinal=1,
        declared_by="creator",
        recorded_at=datetime.now(UTC),
        content=c.content,
    )


@pytest.mark.parametrize(
    "field,value",
    [("actor_ref", "owner"), ("state", "confirmed"), ("visibility", "public"), ("verified", True)],
)
def test_trust_and_visibility_cannot_be_supplied_by_the_browser(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        SaveCredits.model_validate({**declaration().model_dump(), field: value})


@pytest.mark.parametrize(
    "aliases", [("Nova", "nova"), ("",), tuple(str(i) for i in range(9)), ("a" * 81,)]
)
def test_alias_bounds_and_duplicates(aliases: tuple[str, ...]) -> None:
    with pytest.raises(ValidationError):
        CreditContent(aliases=aliases)


def test_organization_cannot_be_linked_to_a_person_account() -> None:
    with pytest.raises(ValidationError):
        Credit(name="Studio", kind="organization", role="direction", actor_ref="ari")


def test_unicode_metadata_is_bounded_by_bytes_not_only_character_count() -> None:
    with pytest.raises(ValidationError, match="metadata byte budget"):
        CreditContent(
            aliases=tuple(chr(0x1F600) * 79 + str(i) for i in range(8)),
            credits=tuple(
                Credit(
                    name=chr(0x1F600) * 78 + str(i),
                    kind="human",
                    role="design",
                    actor_ref=chr(0x1F600) * 64,
                )
                for i in range(12)
            ),
        )


@pytest.mark.parametrize(
    "actor,kind,index", [("creator", "human", 0), ("ari", "agent", 0), ("ari", "human", 1)]
)
def test_only_the_named_human_can_confirm_an_existing_credit(
    actor: str, kind: str, index: int
) -> None:
    c = ConfirmCredit(
        request_id=uuid4(), version_id=uuid4(), profile_id=uuid4(), credit_index=index
    )
    with pytest.raises(AccessDeniedError):
        require_self_confirmation(
            declaration().content,
            c,
            WorkflowActor.model_validate({"actor_ref": actor, "kind": kind}),
        )


def test_unlinked_credit_has_no_self_confirmation_and_valid_credit_can_confirm() -> None:
    c = ConfirmCredit(request_id=uuid4(), version_id=uuid4(), profile_id=uuid4(), credit_index=0)
    actor = WorkflowActor(actor_ref="ari", kind="human")
    require_self_confirmation(declaration().content, c, actor)
    with pytest.raises(AccessDeniedError):
        require_self_confirmation(
            CreditContent(credits=(Credit(name="Ari", kind="human", role="design"),)), c, actor
        )


@pytest.mark.parametrize(
    "field", ["workspace_id", "version_id", "profile_id", "actor_ref", "credit_index"]
)
def test_profile_rejects_unbound_or_wrong_actor_confirmation(field: str) -> None:
    p = profile()
    r = CreditConfirmation(
        id=uuid4(),
        workspace_id=p.workspace_id,
        version_id=p.version_id,
        profile_id=p.id,
        request_id=uuid4(),
        credit_index=0,
        actor_ref="ari",
        recorded_at=datetime.now(UTC),
    )
    update: dict[str, object] = {
        field: 1 if field == "credit_index" else "wrong" if field == "actor_ref" else uuid4()
    }
    with pytest.raises(ValidationError):
        CreditProfile(
            workspace_id=p.workspace_id,
            version_id=p.version_id,
            snapshot=p,
            confirmations=(CreditConfirmation.model_validate({**r.model_dump(), **update}),),
        )


def test_profile_rejects_duplicate_confirmation_and_bounds_credit_count() -> None:
    p = profile()
    r = CreditConfirmation(
        id=uuid4(),
        workspace_id=p.workspace_id,
        version_id=p.version_id,
        profile_id=p.id,
        request_id=uuid4(),
        credit_index=0,
        actor_ref="ari",
        recorded_at=datetime.now(UTC),
    )
    with pytest.raises(ValidationError):
        CreditProfile(
            workspace_id=p.workspace_id, version_id=p.version_id, snapshot=p, confirmations=(r, r)
        )
    with pytest.raises(ValidationError):
        CreditContent(
            credits=tuple(Credit(name=str(i), kind="human", role="design") for i in range(13))
        )
