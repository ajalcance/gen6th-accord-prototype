# 0023. AI Persona Passport as the hackathon prototype

- **Status:** Accepted for prototype scope; implementation and external actions pending
- **Date:** 2026-10-01
- **Deciders:** Albert Alcance, through the scope and documentation instructions in this chat

## Context

The owner is entering AI Builder Cup with Accord and wants a compelling MVP rather than
the entire product roadmap. Discussion selected an AI influencer/persona use case in place
of the initial generic delivery-review example. The owner also requires premium UI/UX
throughout the journey, encrypted private data and verifiable records.

Accord records assertions, evidence and approvals; it does not decide legal ownership.
The roadmap already includes contribution review, claim profiles and Trust; broader
similarity matching and IP registration research remain later work.

## Decision

1. Build **Accord AI Persona Passport**: one persona workflow, creator/reviewer roles,
   creation evidence, contributor records, bounded visual similarity screening, review,
   one campaign authorization and platform-signed export/verification.
2. Follow [the prototype plan](../hackathon/prototype-plan.md) for sequencing and acceptance.
   Five connected screens and meaningful motion are core deliverables; processing states
   must reflect actual server work. Fixture-only design previews are explicitly labelled.
3. Bring forward only a controlled-catalogue similarity experiment from Stage 9. It is
   candidate retrieval for review, not a worldwide originality or facial identity verdict.
4. Reuse the Python/Next.js/Go foundation, Zynth identity boundary and compliance spine.
   Use the approved Google service defaults for the slice. Do not replace identity or
   bypass security because an integration is unavailable; raise a bounded design decision.
5. Preserve workspace privacy, envelope encryption and personal-data separation. A persona
   ID is not an encryption key, and public verification does not grant private evidence access.
6. Demonstrate platform KMS signing first. Creator passkey signing, full log inclusion,
   anchoring and witnesses retain their launch requirements but are outside this prototype.
   Its published labels must describe that narrower assurance.
7. Retain Stage 0–9 as the full product plan. Completing a slice does not complete a stage
   or authorize a production release. Cloud activation, installations and publication
   retain owner-controlled gates.
8. Record intended Accord-only submission scope in [RIGHTS.md](../../RIGHTS.md) and
   [the publication record](../hackathon/publication-record.md). Organizer acknowledgment,
   eligibility and actual submitted inventory remain unresolved. Existing licence stays intact.
9. Record a later owner review of source availability. Six-month timing is tied to confirmed
   event conclusion; no automatic privatization, scheduled job or visibility change is created.

## Consequences

- A visually concrete demo connects all three Accord domains without building every module.
- A [handoff](../hackathon/next-session.md) supplies the next session with durable context.
- Identity readiness, upload safety, matching quality and cloud integration are early risks;
  narrow scope does not permit weakening their controls.
- The public-source requirement conflicts with exposing the private monorepo wholesale.
  Publication packaging and exclusions need review before an owner chooses the source route.
- This ADR is a planning decision subject to the existing owner review and PR gates,
  including the owner-applied guardrail label for ADR files; it edits no checking mechanism.

## Alternatives considered

- **Generic delivery approval:** sound fit, but the owner preferred the AI persona story.
- **Full product implementation:** exceeds the approved MVP scope and event time budget.
- **Government-style IP registration or universal face uniqueness:** unsupported assurance.
- **Immediate monorepo publication:** exposes unrelated private material and is not authorized.
- **Persona generation studio, voice cloning and internet-wide monitoring:** defer to keep
  the prototype focused on evidence, review, authorization and verifiability.
