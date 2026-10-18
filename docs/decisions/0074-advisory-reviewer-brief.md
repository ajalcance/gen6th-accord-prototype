# ADR-0074: Advisory reviewer brief on Gemini

- Status: Accepted for the hackathon prototype; owner enables it per deployment
- Date: 2026-10-17
- Supersedes: None; reuses ADR-0034 session gate, ADR-0055 Google transport and ADR-0053 Gemini rules

## Context

The deployed prototype had no live Google AI path. The existing Gemini adapters compare images and
need the scanner, key wrapper and durable job runtime, none of which are deployed. A reviewer who
opens a saved performer still has to read four free-text fields and work out what is missing before
deciding. That is slow, and it is a natural place for a model to help without deciding anything.

## Decision

1. Add one read-class route, `POST /api/workspaces/{workspace_id}/personas/assistant/brief`. It is
   mounted always and answers 503 until `PERSONA_ASSISTANT_ENABLED` is true. Enabled with a missing
   or invalid project, region or model, startup fails; there is no fallback.
2. The browser sends only a performer id and optional revision. The server resolves the verified
   human actor, reads that version through the existing audited loader (so membership, workspace
   binding and the `persona.version_read` observation apply unchanged), and sends only the four
   creator-written text fields to Gemini on Vertex AI using workload identity. No images, no
   portraits, no evidence, no tool, no URL fetch, no search grounding, no API key.
3. The model is told the fields are untrusted data and must restate, attribute to the creator, list
   missing facts and propose neutral questions. It must not verify, identify, judge ownership,
   consent or quality, or recommend approval. This is a prompt, not a guarantee, so output is also
   constrained: a response schema, one completed candidate, strict length limits, plain text only
   (no markup, control characters or links), and rejection, never repair, of anything else.
4. The response carries the model label, the observed model revision and a fixed server-authored
   notice that the draft is advisory. Nothing is stored. The route writes no row and grants no
   permission, review or approval. Existing independent human review is unchanged.
5. Abuse and cost are bounded in process: ten briefs per actor per ten minutes, four concurrent model
   calls, a 45 second ceiling and a 20 second transport timeout. Any model failure is an opaque 503
   with an incident id in the log and no record content.
6. The browser button is explicit and per click. The page states what text is sent and to whom
   before the click. Rollback is setting `PERSONA_ASSISTANT_ENABLED=false`.

## Consequences

A reviewer gets a short, attributable summary and a list of gaps and questions, and the submission
has a real, demonstrable Google AI path on Cloud Run. The four text fields leave the deployment for
Google. That is data egress and is why the feature is off by default and explicit per click.

The limiter is per instance, so the real ceiling is its limit times the instance count; that is
acceptable for a prototype and is not a quota. A model can still summarise badly or miss an
instruction embedded in a field; the human reviewer remains the control. Output quality, refusal
behaviour and the exact model identifier need a live check before demonstration.

The existing image-comparison adapter still names `gemini-2.5-flash`, which Google retires on
2026-10-20. It is unaffected here because it is not enabled, but it must change before anyone
enables it.

## Alternatives considered

- **Reuse the image comparison provider.** Rejected: it needs deployed infrastructure that does not
  exist and sends biometric images, a much larger disclosure than four text fields.
- **Call Gemini from the browser or with an API key.** Rejected: it breaks the server-side session
  and audit boundary and puts a credential in a client.
- **Persist the brief as a record.** Rejected for now: a stored model opinion invites being read as
  a finding. Persistence needs its own retention and review decision.
- **A new telemetry action.** Rejected: the call is a read of one saved version and reuses
  `persona.version_read`, so the existing coverage guards continue to hold.
