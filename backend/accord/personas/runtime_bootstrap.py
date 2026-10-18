"""Explicit opt-in assembly; constructing providers never calls Google or discovers credentials."""

import base64
import hashlib
import os
import sys
from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from redis.asyncio import Redis

from accord.cache.redis import create_redis, validated_redis_url
from accord.config import Settings
from accord.personas.evidence_crypto import KeyWrapper
from accord.personas.face_crop import LimitedFaceCropper
from accord.personas.face_google import GoogleFaceDetector, GoogleImageEncoder, GoogleTransport
from accord.personas.face_providers import FaceProviders
from accord.personas.google_access import CloudRunAccess
from accord.personas.google_keys import GoogleKeyWrapper, RetainedKeyWrapper
from accord.personas.investigation_google import GoogleInvestigationProvider
from accord.personas.investigation_provider import InvestigationRuntime
from accord.personas.job_runtime import JobRuntime
from accord.personas.passport_google import GooglePassportSigner
from accord.personas.passport_signing import PassportRuntime, PassportTrust
from accord.personas.photo_inspector import PhotoInspector
from accord.personas.runtime_contracts import GoogleRuntimeConfig
from accord.personas.similarity_cache import RedisQueryStore
from accord.personas.similarity_query import SimilarityRuntime
from accord.personas.task_google import GoogleTaskDispatcher
from accord.personas.task_identity import GoogleTaskIdentity


@dataclass(frozen=True)
class PersonaRuntime:
    wrapper: KeyWrapper | None = None
    faces: FaceProviders | None = None
    similarity: SimilarityRuntime | None = None
    investigation: InvestigationRuntime | None = None
    passports: PassportRuntime | None = None
    jobs: JobRuntime | None = None
    task_identity: GoogleTaskIdentity | None = None
    redis: Redis | None = None

    async def close(self) -> None:
        if self.redis is not None:
            await self.redis.aclose()


def read_config(settings: Settings) -> GoogleRuntimeConfig:
    if (
        not settings.persona_api_enabled
        or not settings.persona_photos_enabled
        or sys.platform != "linux"
        or not os.environ.get("K_SERVICE")
        or not 1 <= len(settings.persona_google_config.encode()) <= 65536
    ):
        raise ValueError("Google runtime requires reviewed identity/photos and Cloud Run Linux")
    config = GoogleRuntimeConfig.model_validate_json(settings.persona_google_config)
    if config.workspace_id != settings.persona_workspace_id:
        raise ValueError("Google runtime workspace does not bind identity configuration")
    validated_redis_url(settings)
    return config


def signing(config: GoogleRuntimeConfig, transport: GoogleTransport) -> PassportRuntime:
    keys: dict[str, Ed25519PublicKey] = {}
    for name, encoded in config.trusted_signing_keys.items():
        if len(encoded) != 44:
            raise ValueError("invalid reviewed public trust key")
        raw = base64.b64decode(encoded, validate=True)
        if len(raw) != 32 or base64.b64encode(raw).decode() != encoded:
            raise ValueError("invalid reviewed public trust key")
        keys[name] = Ed25519PublicKey.from_public_bytes(raw)
    signer = (
        GooglePassportSigner(config.signing_version, transport) if config.signing_version else None
    )
    return PassportRuntime(PassportTrust(keys), signer)


def face_providers(config: GoogleRuntimeConfig, transport: GoogleTransport) -> FaceProviders:
    return FaceProviders(
        GoogleFaceDetector(config.project, transport),
        GoogleImageEncoder(config.project, config.region, config.dimensions, transport),
        LimitedFaceCropper(),
    )


def build_runtime(
    settings: Settings,
    inspector: PhotoInspector | None,
    legacy: KeyWrapper | None,
) -> PersonaRuntime:
    if not settings.persona_google_enabled:
        return PersonaRuntime(wrapper=legacy)
    config = read_config(settings)
    if inspector is None:
        raise ValueError("reviewed image inspector required")
    transport = GoogleTransport(CloudRunAccess())
    wrapper = RetainedKeyWrapper(
        GoogleKeyWrapper(
            config.wrapping_version,
            config.retained_wrapping_versions,
            transport,
        ),
        legacy,
    )
    faces = face_providers(config, transport)
    client = create_redis(settings, decode_responses=False)
    similarity = SimilarityRuntime(
        inspector, wrapper, faces, RedisQueryStore(client), config.calibration
    )
    provider = (
        GoogleInvestigationProvider(config.project, config.region, config.gemini_model, transport)
        if config.gemini_model
        else None
    )
    jobs = JobRuntime(
        config.workspace_id,
        hashlib.sha256(config.model_dump_json().encode()).hexdigest(),
        wrapper,
        faces,
        GoogleTaskDispatcher(config.tasks, transport),
    )
    return PersonaRuntime(
        wrapper,
        faces,
        similarity,
        InvestigationRuntime(similarity, provider),
        signing(config, transport),
        jobs,
        GoogleTaskIdentity(config.tasks),
        client,
    )
