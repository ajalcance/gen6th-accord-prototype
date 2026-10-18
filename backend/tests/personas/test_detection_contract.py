"""Rule matching covers inclusions, exclusions, outcomes and trusted severity levels."""

from uuid import uuid4

import pytest

from accord.command.detection import PERSONA_ACTIONS, matches, rules_digest
from accord.command.models import Event
from accord.command.rules import DEFAULT_RULES


@pytest.mark.parametrize(
    "severity,expected", [("critical", True), ("error", False), ("bogus", False)]
)
def test_critical_rule_severity(severity: str, expected: bool) -> None:
    assert (
        matches(DEFAULT_RULES[1], Event(action="persona.version_saved", severity=severity))
        == expected
    )


@pytest.mark.parametrize(
    "action,outcome,expected",
    [
        ("persona.access_denied", "denied", True),
        ("persona.version_saved", "success", False),
        ("client.error", "failure", False),
    ],
)
def test_failure_rule_exclusions(action: str, outcome: str, expected: bool) -> None:
    assert matches(DEFAULT_RULES[3], Event(action=action, outcome=outcome)) == expected


def test_write_rule_and_version_digest() -> None:
    assert matches(DEFAULT_RULES[0], Event(action="persona.version_saved"))
    assert not matches(DEFAULT_RULES[0], Event(action="persona.version_read"))
    assert len(rules_digest()) == 64 and rules_digest() == rules_digest()
    assert PERSONA_ACTIONS == {
        "persona.version_saved",
        "persona.version_read",
        "persona.access_denied",
        "persona.write_conflict",
        "persona.workspace_observed",
        "persona.review_recorded",
        "persona.workflow_observed",
        "persona.campaign_offered",
        "persona.campaign_decided",
        "persona.asset_registered",
        "persona.passport_issued",
        "persona.publication_approved",
        "persona.publication_revoked",
        "persona.publication_observed",
        "persona.evidence_quarantined",
        "persona.evidence_inspected",
        "persona.evidence_read",
        "persona.evidence_purged",
        "persona.portrait_uploaded",
        "persona.portrait_inspected",
        "persona.portrait_bound",
        "persona.portrait_read",
    }
    assert "client.error" not in PERSONA_ACTIONS
    assert uuid4().hex not in PERSONA_ACTIONS
