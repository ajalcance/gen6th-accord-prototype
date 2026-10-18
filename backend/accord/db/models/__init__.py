"""ORM models. Importing this package registers all tables on ``Base.metadata``.

Add your models here and import them below so Alembic autogenerate and the test
test schemas see them, e.g.::

    from accord.db.models.user import User

    __all__ = ["User"]
"""

from accord.command.detection_models import DetectionReceipt
from accord.command.models import AuditLog, Event
from accord.personas.asset_models import AssetEnrollment
from accord.personas.campaign_models import (
    CampaignAsset,
    CampaignDecision,
    CampaignOffer,
    PersonaAsset,
)
from accord.personas.campaign_policy import register_campaign_policies
from accord.personas.capture_models import PortraitCapture, VersionReference
from accord.personas.credit_models import CreditAcceptance, CreditRecord, register_credit_policies
from accord.personas.database_policy import register_policies
from accord.personas.enrollment_policy import register_enrollment_policy
from accord.personas.evidence_models import EvidenceInspection, EvidencePayload, PrivateEvidence
from accord.personas.evidence_policy import register_evidence_policies
from accord.personas.face_models import FaceGeneration
from accord.personas.identity_models import IdentityBinding
from accord.personas.identity_policy import register_identity_policy
from accord.personas.investigation_models import InvestigationRecord
from accord.personas.investigation_review_models import InvestigationReviewRequest
from accord.personas.issuance_models import (
    PassportIssuance,
    PassportPublication,
    PassportUnpublication,
)
from accord.personas.issuance_policy import register_issuance_policy
from accord.personas.job_models import FaceJob, FaceJobTransition
from accord.personas.job_policy import register_job_policy
from accord.personas.lifecycle_models import LifecycleRecord, register_lifecycle_policies
from accord.personas.models import Persona, Version, WorkspaceMember, WriteReceipt
from accord.personas.photo_models import Portrait, PortraitPayload, VersionPortrait
from accord.personas.photo_policy import register_photo_policies
from accord.personas.review_models import ReviewRecord
from accord.personas.review_policy import register_review_policies

register_policies()
register_review_policies()
register_campaign_policies()
register_evidence_policies()
register_identity_policy()
register_photo_policies()
register_job_policy()
register_enrollment_policy()
register_issuance_policy()
register_credit_policies()
register_lifecycle_policies()
__all__: list[str] = [
    "LifecycleRecord",
    "AuditLog",
    "Event",
    "DetectionReceipt",
    "Persona",
    "Version",
    "WorkspaceMember",
    "WriteReceipt",
    "ReviewRecord",
    "PersonaAsset",
    "CampaignOffer",
    "CampaignAsset",
    "CampaignDecision",
    "PrivateEvidence",
    "EvidencePayload",
    "EvidenceInspection",
    "IdentityBinding",
    "Portrait",
    "PortraitPayload",
    "VersionPortrait",
    "PortraitCapture",
    "VersionReference",
    "FaceGeneration",
    "InvestigationRecord",
    "InvestigationReviewRequest",
    "FaceJob",
    "FaceJobTransition",
    "AssetEnrollment",
    "PassportIssuance",
    "PassportPublication",
    "PassportUnpublication",
    "CreditRecord",
    "CreditAcceptance",
]
