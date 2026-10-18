# ADR-0062: Accountable performer lifecycle and controlled use

Date: 2026-10-11. Status: accepted; MVP source prepared, activation pending.

## Context

The owner approved all ten Beijing digital-artist research adaptations, inclusion in the
overall plan, and bounded MVP implementation while Google infrastructure is prepared.
Extend existing records, reviews, production scopes and passports. Accord does not confer
government certification or determine legal ownership.

## Decision

Use an immutable workspace lifecycle ledger, scoped to a performer and exact saved version.
Owner declarations nominate an operator and authority, one to eight time-bounded rights
claims with evidence and withdrawal terms, and explicitly creator-declared provenance.
Authentication alone never proves organizational authority.

Independent reviewers assess operator, rights and content separately, binding the exact
dossier, reviewer, basis statement and expiry. Approval retains server-inspected evidence
digests while originals are clean, retained and unexpired. It is a review attestation, not
automatic legal verification or permission to share private originals. Attestations can
outlive seven-day encrypted payloads. Existing explicit production evidence references
retain their original stricter availability checks. No retention guard is changed.

Replacement invalidates old assessments. Role loss, rights expiry, withdrawal and version
changes invalidate current permission. Production binds the dossier and operator. Private
trial use is capped at 30 days; new uses require new immutable offers and decisions.
Software records permission boundaries; it cannot stop external contract violations.

Members may report concerns. Only independent reviewers respond or suspend; reports alone
do not establish wrongdoing. Suspension applies across performer versions and resolves
per case. Unrelated suspensions remain effective. Performer locks, CAS and exact-request
replay protect changes; history is immutable and paginated.

PERSONA_LIFECYCLE_ENABLED is an explicit schema-accepted activation gate. Disabled routes
deny, preserving the prior deployed contract. Production activation includes lifecycle
enforcement in offer, acceptance, status, export and verification. Clients cannot disable it.
Existing passport projections include production bindings but exclude private dossier data.
Signature integrity remains separate from current use permission.

Future public resolvers, external credentials, format-specific provenance and participation
attestations require separate contracts. Draft Chinese measures are inspiration, not an
enacted-law compatibility claim. [Complete scope register](../hackathon/performer-lifecycle.md).

## Acceptance

Prepare migration 0018lifecycle and confined grants; execute neither here. Register routes
under existing server-observed telemetry/detection/audit/compliance actions. Test independent
review, evidence/expiry, replay/CAS, suspension, policy binding, legacy serialization,
HTTP bounds, SQL/RLS/immutability and UI recovery. Live SQL/sessions, rendered acceptance
and release-revision CI remain separate gates.
