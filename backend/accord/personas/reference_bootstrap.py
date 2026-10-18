"""Independent reference assembly; no browser, scanner, Redis or signing providers."""

import hashlib
import os
import sys
from dataclasses import dataclass

from sqlalchemy.engine import make_url

from accord.config import DatabaseTransport, Environment, Settings
from accord.db.runtime import validated_database_url
from accord.personas.face_google import GoogleTransport
from accord.personas.google_access import CloudRunAccess
from accord.personas.google_keys import GoogleKeyWrapper, RetainedKeyWrapper
from accord.personas.job_runtime import JobRuntime
from accord.personas.runtime_bootstrap import face_providers
from accord.personas.runtime_contracts import GoogleRuntimeConfig
from accord.personas.task_google import GoogleTaskDispatcher
from accord.personas.task_identity import GoogleTaskIdentity


@dataclass(frozen=True)
class ReferenceRuntime:
    jobs: JobRuntime
    identity: GoogleTaskIdentity


def reference_config(settings: Settings) -> GoogleRuntimeConfig:
    """Require explicit production reference transport/scope; never enable API flags."""
    try:
        if (
            settings.environment is not Environment.PRODUCTION
            or not settings.persona_google_enabled
            or settings.persona_api_enabled
            or settings.persona_photos_enabled
            or sys.platform != "linux"
            or not os.environ.get("K_SERVICE")
            or settings.database_transport is not DatabaseTransport.CLOUD_SQL_PROXY
            or not 1 <= len(settings.persona_google_config.encode()) <= 65536
        ):
            raise ValueError
        address = make_url(validated_database_url(settings))
        if address.username != "accord_reference" or address.database != "appdb":
            raise ValueError
        config = GoogleRuntimeConfig.model_validate_json(settings.persona_google_config)
        if config.workspace_id != settings.persona_workspace_id:
            raise ValueError
        return config
    except Exception:
        raise ValueError("reviewed production reference configuration required") from None


def build_reference(settings: Settings) -> ReferenceRuntime:
    """Construct lazy adapters only; retain the API's exact full configuration binding."""
    config = reference_config(settings)
    transport = GoogleTransport(CloudRunAccess())
    wrapper = RetainedKeyWrapper(
        GoogleKeyWrapper(config.wrapping_version, config.retained_wrapping_versions, transport),
        None,
    )
    runtime = JobRuntime(
        config.workspace_id,
        hashlib.sha256(config.model_dump_json().encode()).hexdigest(),
        wrapper,
        face_providers(config, transport),
        GoogleTaskDispatcher(config.tasks, transport),
    )
    return ReferenceRuntime(runtime, GoogleTaskIdentity(config.tasks))
