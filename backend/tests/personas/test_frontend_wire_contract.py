"""Shared fictional wire examples are accepted by the actual backend contracts."""

import json
from pathlib import Path

import pytest
from pydantic import BaseModel

from accord.personas.campaign_contracts import (
    CampaignDecisionCommand,
    CampaignDecisionPage,
    CampaignDecisionReceipt,
    CampaignReceipt,
    CampaignStatus,
    OfferCampaignCommand,
)
from accord.personas.contracts import PersonaVersion
from accord.personas.evidence_contracts import EvidenceSnapshot
from accord.personas.gallery import GalleryPage, GalleryQuery
from accord.personas.service import SaveCommand
from accord.personas.workflow_contracts import ReviewCommand, ReviewPage, ReviewSnapshot
from accord.personas.workflow_evidence_contracts import WorkflowEvidence

WIRE = Path(__file__).resolve().parents[3] / "frontend/tests/fixtures/persona-wire.json"


@pytest.mark.parametrize(
    "name,model",
    [
        ("save", SaveCommand),
        ("version", PersonaVersion),
        ("reviewCommand", ReviewCommand),
        ("review", ReviewSnapshot),
        ("offer", OfferCampaignCommand),
        ("campaign", CampaignReceipt),
        ("decisionCommand", CampaignDecisionCommand),
        ("decision", CampaignDecisionReceipt),
        ("status", CampaignStatus),
        ("galleryQuery", GalleryQuery),
        ("gallery", GalleryPage),
        ("reviewHistory", ReviewPage),
        ("campaignHistory", CampaignDecisionPage),
        ("evidenceStatus", EvidenceSnapshot),
        ("workflowEvidence", WorkflowEvidence),
    ],
)
def test_frontend_examples_match_backend(name: str, model: type[BaseModel]) -> None:
    examples = json.loads(WIRE.read_text(encoding="utf-8"))
    parsed = model.model_validate(examples[name])
    assert parsed.model_dump(mode="json") == examples[name]
