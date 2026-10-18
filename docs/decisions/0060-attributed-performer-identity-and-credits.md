# ADR-0060: Attributed performer identity and contributor credits

Date: 2026-10-06
Status: Accepted for owner-approved MVP source implementation; runtime activation pending

## Context

The owner reviewed an ORCID comparison and approved the recommended MVP additions, asking
that every comparison item also remain in the future-development plans. Accord already has
continuing performer IDs, immutable appearance versions, workspace sessions, evidence and
production permissions. Contribution text alone cannot distinguish a creator's declaration
from a contributor's authenticated acknowledgment. Existing reviews and signed passports
cannot silently acquire new claims after they were issued.

## Decision

Expose the existing performer UUID prominently with copy, workspace scope, saved-version
attribution and receipt time. Names, face representations, account IDs and signing keys serve
different purposes. A performer ID survives renaming/version changes; it is neither a unique
face number nor a public resolver, government identity or proof of ownership.

Add bounded optional aliases and structured human/organization credits as append-only
annotations of one saved version. Only its owner with the creator role may declare/replace
them, against the current version and expected prior declaration. Store at most eight aliases
and twelve credits, with a 10,000-byte content budget and 12,288-byte request limit. Each credit
names a role and optionally a workspace account or owner-held exact-version evidence reference.
Naming an account does not invite it, grant access or authenticate its participation.

Only the named authenticated human may confirm their own role. Bind the receipt to workspace,
version, declaration ID and credit slot; replacing the declaration requires fresh confirmations.
Display creator-declared and contributor-confirmed separately. Organization names remain
declarations; no organization attestation is implemented. Replays preserve actor and exact
intent; membership is rechecked and stale/new conflicting requests fail closed.

Use two immutable, forced-RLS tables (`persona_credit_profiles`,
`persona_credit_confirmations`) separate from existing version and passport shapes. Existing
reviews/exports do not include or certify annotations. Linking evidence exposes only its
reference to authorized workspace members, not its private attachment. All annotation metadata
is workspace-visible; field-level sharing is future work. Never publish credits implicitly.

Reuse verified sessions, transaction tracking, exact-retry recovery and the existing audited
`persona.workspace_observed` event with minimal operation metadata. Register all three new
routes in telemetry/detection/audit/compliance coverage. Do not log raw aliases or credits.
Prepare migration `0017credits` and SELECT/INSERT-only runtime grants; default
`PERSONA_CREDITS_ENABLED=false` prevents new-table access before approved activation.
Populated history cannot be downgraded away. No migration, grant or configuration activation
is performed by this implementation.

Show bounded production history for the selected saved version using existing authorized
offers, scope, asset references, permission status and decision history. Expand an entry to
read its current state. An offer, acceptance or permission does not establish actual appearance
in a production. A production participation attestation needs a later reviewed contract.

## Consequences and future direction

This extends the bounded prototype without an ORCID integration, new package, provider call,
public identifier service or delegated-access policy. Source tests and synthetic sessions do
not establish SQL/RLS, live-account or rendered acceptance.

[Development register](../hackathon/performer-identity-and-credits.md) retains all eight comparison
items with stable IDs, boundaries and acceptance criteria. Accept their direction, not their
future implementation or activation: public resolvers, authenticated organization associations,
claim-level review, granular visibility, production attestations/external works, delegates,
import review and duplicate/correction/dispute workflows require separate implementation ADRs.
They must preserve historical attribution, explicit permission, revocation and human review.
