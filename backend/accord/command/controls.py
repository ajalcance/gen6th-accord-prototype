"""Compliance control catalog + action→control mapping (the "rules are data" pattern).

Every audited action declares which controls it provides evidence for; the audit worker stamps
those onto each entry's ``compliance_tags``. Coverage is enforced: every emitted action maps to
>=1 control or is in ``CONTROL_EXEMPT`` — a new action can't ship without a compliance decision.

Replace/extend this starter catalog with your frameworks.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..telemetry.registry import CLIENT_ACTIONS


@dataclass(frozen=True, slots=True)
class Control:
    """One compliance control an action can be evidence for."""

    id: str
    framework: str
    clause: str
    title: str
    family: str


CONTROLS: tuple[Control, ...] = (
    Control("SOC2_CC7.2", "SOC2", "CC7.2", "Monitor components for anomalies", "Monitoring"),
    Control("SOC2_CC7.3", "SOC2", "CC7.3", "Evaluate & respond to security events", "Monitoring"),
    Control("ISO27001_A8.15", "ISO27001", "A.8.15", "Logging", "Logging"),
    Control("ISO27001_A8.16", "ISO27001", "A.8.16", "Monitoring activities", "Logging"),
)
CONTROLS_BY_ID: dict[str, Control] = {c.id: c for c in CONTROLS}
FRAMEWORKS: tuple[str, ...] = ("SOC2", "ISO27001")

# action → controls it provides evidence for.
ACTION_CONTROLS: dict[str, tuple[str, ...]] = {
    "command.persona_detection_evaluated": ("SOC2_CC7.2", "ISO27001_A8.16"),
    "auth.session_observed": ("ISO27001_A8.15",),
    "workspace.membership_provisioned": ("ISO27001_A8.15",),
    "persona.version_saved": ("ISO27001_A8.15",),
    "persona.portrait_uploaded": ("ISO27001_A8.15",),
    "persona.portrait_inspected": ("SOC2_CC7.3", "ISO27001_A8.15"),
    "persona.portrait_bound": ("ISO27001_A8.15",),
    "persona.portrait_read": ("ISO27001_A8.15",),
    "persona.evidence_quarantined": ("ISO27001_A8.15",),
    "persona.evidence_inspected": ("SOC2_CC7.3", "ISO27001_A8.15"),
    "persona.evidence_read": ("ISO27001_A8.15",),
    "persona.evidence_purged": ("ISO27001_A8.15",),
    "persona.version_read": ("ISO27001_A8.15",),
    "persona.access_denied": ("SOC2_CC7.3", "ISO27001_A8.15"),
    "persona.write_conflict": ("ISO27001_A8.15",),
    "persona.workspace_observed": ("SOC2_CC7.2", "ISO27001_A8.16"),
    "persona.review_recorded": ("ISO27001_A8.15",),
    "persona.workflow_observed": ("ISO27001_A8.15",),
    "persona.asset_registered": ("ISO27001_A8.15",),
    "persona.passport_issued": ("ISO27001_A8.15",),
    "persona.publication_approved": ("ISO27001_A8.15",),
    "persona.publication_revoked": ("ISO27001_A8.15",),
    "persona.publication_observed": ("ISO27001_A8.15",),
    "persona.campaign_offered": ("ISO27001_A8.15",),
    "persona.campaign_decided": ("ISO27001_A8.15",),
}

# Actions deliberately NOT compliance evidence. Per-action judgement calls (routine reads) are
# added by name; every client-reported action is included by set union, because ADR-0012 makes
# that exemption invariant — an auditor asking "prove this happened" needs an observation, and
# a client report is a claim. Useful operationally, worthless as attestation.
CONTROL_EXEMPT: frozenset[str] = frozenset() | CLIENT_ACTIONS


def controls_for(action: str) -> list[str]:
    """The control ids an action provides evidence for (sorted; empty if exempt/unknown)."""
    return sorted(ACTION_CONTROLS.get(action, ()))
