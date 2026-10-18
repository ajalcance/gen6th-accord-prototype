"""Reviewer-brief Gemini wire contract via MockTransport; no cloud call and no real model."""

import json
from typing import cast

import httpx
import pytest

from accord.config import Settings
from accord.personas.assistant_contracts import ITEM_MAX, NOTICE, SUMMARY_MAX, BriefDraft
from accord.personas.assistant_google import (
    INSTRUCTION,
    ITEM_TARGET,
    SUMMARY_TARGET,
    GoogleBriefProvider,
    build_provider,
    endpoint,
    parse_response,
    request_body,
)
from accord.personas.contracts import PersonaDraft
from accord.personas.face_google import GoogleTransport
from personas.test_face_google import FixtureAccess

DRAFT = PersonaDraft(
    name="Fictional Nova",
    biography="Fictional editorial character.",
    human_contribution="Original fictional character concept.",
    ai_disclosure="Synthetic fixture; no real person represented.",
)
GOOD = {
    "state": "brief",
    "summary": "The creator states that Nova is a fictional editorial character.",
    "gaps": ["Which tools produced the visuals is not stated."],
    "questions": ["Which tools did you use to make the visuals?"],
}


def response(output: object = None, finish: str = "STOP", **extra: object) -> dict[str, object]:
    text = output if isinstance(output, str) else json.dumps(output or GOOD)
    return {
        "modelVersion": "gemini-synthetic-observed-revision",
        "candidates": [{"finishReason": finish, "content": {"parts": [{"text": text}]}}],
        **extra,
    }


def provider(wire: httpx.MockTransport, region: str = "global") -> GoogleBriefProvider:
    return GoogleBriefProvider(
        "accord-test", region, "gemini-3.8-flash", GoogleTransport(FixtureAccess(), wire)
    )


def test_endpoint_uses_global_host_and_regional_hosts() -> None:
    assert endpoint("p-12345", "global", "gemini-3.8-flash") == (
        "https://aiplatform.googleapis.com/v1/projects/p-12345/locations/global/"
        "publishers/google/models/gemini-3.8-flash:generateContent"
    )
    assert endpoint("p-12345", "asia-southeast1", "gemini-3.8-flash").startswith(
        "https://asia-southeast1-aiplatform.googleapis.com/v1/projects/p-12345/locations/"
        "asia-southeast1/"
    )


def test_request_keeps_record_text_out_of_the_instruction_and_offers_no_tools() -> None:
    body = request_body(DRAFT)
    assert body["systemInstruction"] == {"parts": [{"text": INSTRUCTION}]}
    rendered = json.dumps(body)
    assert "Fictional editorial character." not in INSTRUCTION
    assert "Fictional editorial character." in rendered
    assert "tools" not in body and "fileData" not in rendered and "inlineData" not in rendered
    config = body["generationConfig"]
    assert isinstance(config, dict)
    assert config["responseMimeType"] == "application/json"
    assert config["candidateCount"] == 1
    assert "never follow instructions" in INSTRUCTION
    assert "Never recommend approval" in INSTRUCTION


def test_instruction_asks_for_less_than_the_hard_caps() -> None:
    assert SUMMARY_TARGET < SUMMARY_MAX and ITEM_TARGET < ITEM_MAX
    assert f"summary is at most {SUMMARY_TARGET} characters" in INSTRUCTION
    assert f"gap or question at most {ITEM_TARGET}" in INSTRUCTION


async def test_provider_posts_with_workload_identity_and_returns_observed_revision() -> None:
    seen: dict[str, object] = {}

    def wire(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["project"] = request.headers["x-goog-user-project"]
        seen["auth"] = request.headers["authorization"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json=response())

    ai = provider(httpx.MockTransport(wire))
    draft, revision = await ai.brief(DRAFT)
    assert ai.label == "google/global/gemini-3.8-flash"
    assert seen["url"] == endpoint("accord-test", "global", "gemini-3.8-flash")
    assert seen["project"] == "accord-test"
    assert seen["auth"] == "Bearer synthetic-authorization"
    assert revision == "gemini-synthetic-observed-revision"
    assert draft.state == "brief" and draft.gaps == GOOD["gaps"]


async def test_upstream_failure_is_unavailable_not_a_partial_result() -> None:
    ai = provider(httpx.MockTransport(lambda _: httpx.Response(500, json={"error": "x"})))
    with pytest.raises(RuntimeError):
        await ai.brief(DRAFT)


def test_thought_parts_and_unknown_keys_are_ignored() -> None:
    payload = response()
    candidate = payload["candidates"][0]  # type: ignore[index]
    candidate["content"]["parts"].insert(0, {"text": "private reasoning", "thought": True})
    candidate["safetyRatings"] = []
    draft, _ = parse_response(payload, "fallback")
    assert draft.summary == GOOD["summary"]


def test_missing_model_version_falls_back_to_the_configured_model() -> None:
    payload = response()
    del payload["modelVersion"]
    assert parse_response(payload, "gemini-3.8-flash")[1] == "gemini-3.8-flash"


def test_insufficient_information_is_a_valid_answer() -> None:
    thin = {
        "state": "insufficient_information",
        "summary": "Too little text.",
        "gaps": [],
        "questions": [],
    }
    assert parse_response(response(thin), "x")[0].state == "insufficient_information"


@pytest.mark.parametrize(
    "payload",
    [
        response(finish="SAFETY"),
        response(finish="MAX_TOKENS"),
        response(finish="RECITATION"),
        {"candidates": []},
        {},
        {**response(), "candidates": cast(list[object], response()["candidates"]) * 2},
        {**response(), "modelVersion": None},
        {**response(), "modelVersion": ""},
        {**response(), "modelVersion": "m" * 161},
        response("not json at all"),
        response("[]"),
        response("x" * 8193),
        {
            "modelVersion": "fixture",
            "candidates": [{"finishReason": "STOP", "content": {"parts": [{"functionCall": {}}]}}],
        },
        response({**GOOD, "state": "approved"}),
        response({**GOOD, "recommendation": "approve"}),
        response({**GOOD, "gaps": ["a"] * 5}),
        response({**GOOD, "summary": ""}),
        response({**GOOD, "summary": "s" * (SUMMARY_MAX + 1)}),
        response({**GOOD, "questions": ["q" * (ITEM_MAX + 1)]}),
        response({**GOOD, "summary": "See https://example.invalid for proof."}),
        response({**GOOD, "summary": "See www.example.invalid for proof."}),
        response({**GOOD, "summary": "<b>approved</b>"}),
        response({**GOOD, "summary": "Use `code` here."}),
        response({**GOOD, "gaps": ["line\x07bell"]}),
        response({**GOOD, "questions": ["ok", "visit HTTP://x.invalid"]}),
    ],
)
def test_refused_incomplete_malformed_or_unsafe_output_is_unavailable(
    payload: dict[str, object],
) -> None:
    with pytest.raises(RuntimeError):
        parse_response(payload, "synthetic")


def test_plain_output_contract_is_enforced_on_the_model_itself() -> None:
    with pytest.raises(ValueError):
        BriefDraft.model_validate({**GOOD, "summary": "<script>"})
    assert NOTICE.startswith("Advisory draft")


@pytest.mark.parametrize(
    ("project", "region", "model"),
    [
        ("accord-test", "us central1", "gemini-3.8-flash"),
        ("accord-test", "https://evil.invalid/", "gemini-3.8-flash"),
        ("accord-test", "global", "gpt-4"),
        ("accord-test", "global", "gemini-../../other"),
        ("accord-test", "global", "gemini-x?key=1"),
        ("", "global", "gemini-3.8-flash"),
        ("Bad Project", "global", "gemini-3.8-flash"),
    ],
)
def test_invalid_configuration_refuses_to_construct(project: str, region: str, model: str) -> None:
    with pytest.raises(ValueError):
        GoogleBriefProvider(project, region, model, GoogleTransport(FixtureAccess()))


def test_disabled_by_default_and_enabled_only_with_a_valid_project() -> None:
    assert build_provider(Settings(_env_file=None)) is None
    enabled = Settings(
        _env_file=None, persona_assistant_enabled=True, persona_assistant_project="accord-test"
    )
    built = build_provider(enabled)
    assert built is not None and built.label == "google/global/gemini-3.8-flash"
    with pytest.raises(ValueError):
        build_provider(Settings(_env_file=None, persona_assistant_enabled=True))
