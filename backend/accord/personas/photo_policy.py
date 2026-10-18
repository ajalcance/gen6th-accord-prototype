"""Portrait metadata/bindings/payloads cannot be changed by the runtime role."""

from typing import cast

from sqlalchemy import Table, event

from accord.personas.capture_models import PortraitCapture, VersionReference
from accord.personas.database_policy import execute_ddl, immutable_trigger, policies
from accord.personas.face_models import FaceGeneration
from accord.personas.investigation_models import InvestigationRecord
from accord.personas.investigation_review_models import InvestigationReviewRequest
from accord.personas.job_models import FaceJob, FaceJobTransition
from accord.personas.models import Version
from accord.personas.photo_models import Portrait, PortraitPayload, VersionPortrait


def register_photo_policies() -> None:
    # Metadata-created SQL tests need Version's shared trigger function before this table.
    cast(Table, Portrait.__table__).add_is_dependent_on(cast(Table, Version.__table__))
    for model in (
        Portrait,
        PortraitPayload,
        VersionPortrait,
        PortraitCapture,
        VersionReference,
        FaceGeneration,
        InvestigationRecord,
        InvestigationReviewRequest,
        FaceJob,
        FaceJobTransition,
    ):
        for statement in policies(model.__tablename__):
            event.listen(model.__table__, "after_create", execute_ddl(statement))
        event.listen(
            model.__table__, "after_create", execute_ddl(immutable_trigger(model.__tablename__))
        )
