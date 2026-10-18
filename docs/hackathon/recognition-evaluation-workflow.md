# Recognition evaluation workflow

Prepared 2026-10-06. Source workflow implemented; actual recognition accuracy is unmeasured.
This advances the permitted-corpus milestone after S8–S10 without activating infrastructure.
See [ADR-0058](../decisions/0058-offline-recognition-evidence.md) and the
[benchmark protocol](matching-benchmark-plan.md).

## Private inputs

The owner supplies a local corpus with permission/provenance records and two JSON inputs.
Keep real images, permission documents and vectors out of git. No nonignored corpus or manifest
was found in the repository inventory on October 6; no private corpus location was supplied.
No images were generated, downloaded or sent to a provider for this work.

Manifest: `assets` array; each row has `id`, `family`, `split` (development/calibration/test),
`role` (reference/query), `case` (regenerated/lookalike/absent), `sha256`, `permission_record`,
`synthetic: true` and optional `relative_path`. A corpus byte check requires every relative path.
Asset IDs and file digests must be unique; performer families cannot cross splits. Known queries
have references in their split, absent queries do not. Test queries include all three cases.
Permission references are owner declarations; validation does not independently grant rights.

Observations: `model`, `revision`, `role` (face/whole_image), `observations` array. Every permitted
asset appears once with matching `asset_id`/`sha256`, compatible numeric `vector` or null,
finite nonnegative `latency_ms`, and numeric `cost_usd` or null/omitted when unknown.
Do not invent zero cost for missing usage. Null vectors record failed attempts, not rejection.
Vectors must originate from the approved capture/encoder process, not display thumbnails.
Record recipes, resolved provider revisions, timestamps/errors/usage and ranked reference traces
separately under the full protocol. This aggregate evaluator does not establish those facts.

## Run and review

Inspect the CLI from the repository using its existing Python environment:

```sh
env PYTHONPATH=backend backend/.venv/bin/python -m accord.personas.face_benchmark_runner --help
```

Use `backend` as the working directory for the actual run, with explicit private input paths:

```sh
.venv/bin/python -m accord.personas.face_benchmark_runner /absolute/private/manifest.json /absolute/private/observations.json --corpus-root /absolute/private/corpus
```

Save stdout privately as the report JSON. The command checks confined resolved paths, byte
budgets and all digests before reporting `bytes_checked`. That label is only a CLI assertion
about source bytes; it does not verify image safety, legal provenance or provider execution.
The root and files must remain owner-controlled during the run; this is not a hostile filesystem
sandbox. Omit the corpus flag only for deliberately unchecked supplied-observation evaluation.

In the frontend, open Connection & readiness → Recognition benchmark evidence → Choose
benchmark report JSON. The report stays in that panel's browser memory and is cleared when the
panel closes or another file is selected. No upload, storage, runtime policy write or cloud cost.
Inputs and viewer imports are bounded at 16 MiB. Invalid/stale reports cannot restore old results.

Read all three case rows with their denominators. Recall includes failed known queries.
False matches/scored excludes failed and reference-unavailable queries; zero on an unscored
case is shown as unmeasured. Latency covers all supplied observations, including reference
encoding and development/calibration; it is not end-to-end search response latency.
Unknown cost keeps total unknown and displays the known subtotal. Canonical manifest/run
fingerprints bind normalized submitted inputs; they are not signatures or independent evidence.

## Remaining measured acceptance and Google rehearsal

1. Supply permitted images and provenance, review family identities/independent lookalikes and
   sample sizes, then freeze development recipes and operating decisions before held-out use.
2. Approve exact Google region/model/revision, identity, privacy, quota and spend bounds. Execute
   actual capture/detection/face and whole-image encoders; retain byte bindings and provider logs.
3. Run actual held-out comparisons and review recall, failures, false matches, ambiguity/margin,
   per-query/reference traces, latency and cost. Inspect sample adequacy; this report has no
   confidence intervals or automatic pass threshold. Select the production policy separately.
4. Complete [S7 activation/rehearsal prerequisites](google-runtime-slice.md), actual SQL/RLS,
   scanner/Linux/Redis/IAM/key checks, reviewer journey and rendered accessibility acceptance.

No SDK installation, cloud/model request, migration, grant, restart, key activation, publication
or submission occurred. Those owner gates remain as recorded in the existing prototype plan.

## Validation

Twenty-five focused backend arithmetic/corpus/CLI tests pass; all 471 frontend tests in 55 files
pass, including report import, invalid replacement, stale completion and existing layout checks.
Ruff/Black, mypy over 337 files, Bandit, frontend ESLint/Prettier/types and production build pass.
Shared client bundle remains 166.4 kB gzip against 250 kB. Scoped Semgrep scans seven changed
source files with eleven rules and zero findings; redacted gitleaks scans persona backend,
frontend libraries and passport UI with no leaks. Doc guards and whitespace checks pass.

Full check guard tests pass (776, 18 skipped), policy/harness and backend static checks pass.
An initial test import naming error was corrected, without changing a guard. The backend gate
then stops at pip-audit's temporary pip upgrade failure; frontend gate stops at npm audit DNS
failure (`ENOTFOUND registry.npmjs.org`). No audit success, full-green, Docker-backed SQL/coverage
or rendered/live recognition acceptance is claimed. Existing source remains in the dirty checkout;
no commit, PR, deployment or owner-policy change occurred.
