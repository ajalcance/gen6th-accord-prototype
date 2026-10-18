# Accountable performer lifecycle development register

Owner approval: 2026-10-11. [ADR-0062](../decisions/0062-accountable-performer-lifecycle.md).
This extends the [ORCID register](performer-identity-and-credits.md), retaining every O1-O8 item.
Source preparation, automated evidence, live acceptance and deployment are separate statuses.

## All ten approved adaptations

| ID | Feature/process | MVP source target | Later development and acceptance |
|---|---|---|---|
| L1 | Accountable operator | Named workspace human, organization/authority declaration, evidence, independent assessment | Organization representatives, account picker, least-privilege delegates; authentication is not authority. |
| L2 | Rights and consent | Likeness/voice/source performance/artwork/other claims, scope, evidence, dates, withdrawal terms | Claim-level recipient consent and revocable agreements; attestations never extend underlying rights. |
| L3 | Individual requirements | Operator, rights and content reviews with dossier, reviewer, basis and expiry | Per-claim review methods and jurisdictional policy packs; no blanket verified badge. |
| L4 | Controlled trials | Named production/assets/recipient/conditions/duration; private trials up to 30 days | Pilot completion and broader-use application; trials do not automatically become unrestricted permission. |
| L5 | Reassessment | New dossier requires new reviews; exact production binding, version/role/expiry checks | Explicit material model/voice/reference changes and explanations of invalidated assurances. |
| L6 | Concerns/suspension | Workspace report, independent response, performer-wide suspension, immutable history | Party responses, appeals, preferences/notifications and authorized public reporting; no automatic finding of wrongdoing. |
| L7 | Current passport status | Extend existing fresh permission checks and production bindings; integrity separate | Opt-in minimal resolver, cache invalidation and issuer lifecycle; offline signatures do not prove current permission. |
| L8 | Provenance/disclosure | Creator-declared method/provider/model/disclosure and separate content review | Format-specific extraction/export, C2PA/other interoperability after conformance tests; absent metadata proves nothing about origin. |
| L9 | External credentials | Roadmap retained | Issuer/id/jurisdiction/scope/expiry, evidence, verification and revocation; uploads remain supplied claims until checked. |
| L10 | Production operating record | Roadmap; existing offer/decision history retained | Operator, actual use/completion/incidents and recipient attestations; permission is not proof of appearance. |

## Integrated journey and privacy

System Capture registers identity/reference. Saved record -> Rights & operator records
authority, rights, provenance and concerns. Independent reviewers assess the exact dossier.
Production & use binds a trial/production offer. Passports checks fresh status and integrity.
Existing private evidence intake stores originals; lifecycle fields contain references only.

Reviewer statements and captured evidence hashes are durable attestations, not certificates
of ownership or proof the reviewer accessed originals. Reviewers must state their basis.
Existing evidence expiry and authorized purge rules remain intact; automatic deletion is not
claimed. Existing production evidence references
still require available originals; dossier attestations have separate expiry/replacement and
withdrawal history. Private dossier fields are excluded from public and portable projections.

## Sequencing

1. Implement and verify bounded L1-L8 source; retain all later acceptance criteria above.
2. Disposable SQL tests: migrations, confined roles, tenant RLS, replay, concurrency and immutability.
3. Real owner/reviewer sessions and rendered desktop/mobile, retry/cancel, trial and suspension review.
4. Combine with reviewed [Google/Zynth G0-G8](../runbooks/google-production-bootstrap.md).
5. One coordinated artifact/PR/CI/release review; activate lifecycle only with accepted schema/grants.

## Sources

- [Beijing sandbox](https://kfqgw.beijing.gov.cn/zwgkkfq/2024zcjd/202606/t20260616_4702349.html): trial, review, supervision and exit.
- [AI-content labels](https://www.cac.gov.cn/2025-03/14/c_1743654684782215.htm): existing disclosure/metadata rules.
- [Digital-human draft](https://www.cac.gov.cn/2026-04/03/c_1776952992709096.htm): consent/contracts/concerns; final enactment unverified.

These are adapted product patterns. Face registration, clean inspection and signatures do
not grant a government license. No government integration or legal compliance claim is implied.

## Evidence

L1–L8 MVP source is prepared. The journey uses compact forms, explicit confirmation, same-intent
retry/cancellation recovery, failure states and on-demand paginated history. Private trial scope
does not grant public use; separate approval of public metadata still follows existing policy.

October 11 automated evidence:

- 514 frontend tests pass; TypeScript, ESLint and Prettier pass. Isolated Node 22 production
  build passes; shared client bundle is 167.0 kB gzipped against the existing 250 kB budget.
- 39 targeted backend cases and 104 adjacent contract/signing/HTTP/telemetry regressions pass.
  Tests use synthetic sessions and injected services; they are not live identity/provider proof.
- Ruff/Black/mypy/Bandit and `make dod-check` pass. Full `make check` passes 776 guard tests
  (18 skipped), policy, harness and backend static checks, then fails at pip-audit's temporary
  pip/wheel/setuptools bootstrap. SQL/coverage, Trust and docs-site phases were not reached.
- Seven lifecycle PostgreSQL cases collect, covering persistence/RLS/immutability, constraint integrity, concurrency,
  cross-version and hidden/multiple-case suspension; execution remains owner/CI pending.

Remaining acceptance: full dependency/CI gate; disposable migration/model/grant parity and SQL
isolation; real creator/operator/reviewer/recipient sessions; rendered desktop/mobile/access-loss
review; original retention and approved rights evidence; Google/Zynth G0–G8. Enable lifecycle only
after these prerequisites. Existing unbound permissions become ineligible under enabled policy
and require new reviewed offers. A populated ledger refuses destructive downgrade.

Later owner full-check tail: **795 passed, 2 failed, 307 ProgrammingError errors; 81.25% coverage**.
The detection contract and migration reversal fail; SQL setup errors include lifecycle cases.
No full PostgreSQL traceback was supplied, so SQL execution is attempted/failed, not accepted.
See [current owner/cloud evidence](../runbooks/google-production-inventory-2026-10-11.md) and
[next-chat diagnosis](next-session-2026-10-11.md). Earlier focused tests remain historical evidence.

Migration/grants and lifecycle activation remain pending. Owner Google foundation/key provisioning
is recorded separately; no application deployment, publication or Git write occurred in this update.
Checkout/HEAD are preserved; release preparation must include all previously uncommitted work.
