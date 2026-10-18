# ADR-0038: Private, integrity-pinned braces depth backport

- Status: **Owner approved artifact adoption, installation and maintenance; implemented and owner local validation passes; PR review pending**
- Date: 2026-10-03
- Review unit: dependency remediation for frontend and docs-site, separate from persona writes

## Context

The corrected owner backend suite and Trust checks pass. The unchanged frontend audit
blocks on GHSA-vfj7-8cjw-p6xm. Both apps have braces 3.0.3 through the pinned Next lint plugin.
The advisory lists no patched release. A forced lint downgrade loses compatibility and is
not selected. The fetched pillarsdotnet fork at 82d539e412aa2f6034dabdf3d51f5ee36036cfe7
guards default depth but includes unreleased parser changes and inconsistent fractional
limits. A direct tinyglobby substitution changes root-directory matches. Neither candidate
is selected for installation.

## Owner-approved decision

Maintain a private braces 3.0.4-accord.1 package derived from the published 3.0.3 source at
74b2db2938fad48a2ea54a9c8bf27a37a62c350d. Apply only the reviewed five-file depth patch;
retain entry point, utilities and MIT license. Pin fill-range to the already installed 7.1.1.
The package has no lifecycle scripts. Do not publish it to any registry.

Store the reviewed tarball, readable source, patch and provenance under vendor/braces. Mirror
the same tar bytes under each app's vendor/braces so the existing frontend Docker context
contains its dependency; COPY the tar before npm ci. No release workflow change is required.
Each app directly pins braces as a devDependency to file:vendor/braces/braces-3.0.4-accord.1.tgz
and scopes micromatch@4.0.8 -> braces -> 3.0.4-accord.1. A bare local-file override resolves
relative to micromatch in npm's fetch path; this exact version deduplicates to the directly
pinned local artifact. npm 10 and npm 11 both validate docs-site's installed dependency tree.
Generate locks with the existing npm 11.16.0 resolver: only the root devDependency and braces
package record change. npm 10's unrelated platform-metadata drift was rejected. Other
dependency drift is refused. No gate command, scanner configuration or Next rule is changed.

Artifact SHA-256:
2155cb703acd5f4247164321feb72df40214676b5cc7c362060f56e64e33bf7c

Artifact SHA-512 integrity:
sha512-mq+bKmdbUUTDiQZqhfUAA4DnYOW5iAhcXBq7VtQ8SD4rvfSsvL5gEwWMJ4o8YNSWNlRW6toXlKNhFDHaBP0Oaw==

## Verification and acceptance

The 764 released cases pass under Node 22's built-in test runner using a synchronous adapter
for Mocha globals; no fixture shell invocation occurs. One additional provenance test passes.
The original published package passes the same released cases. Each app's installed consumer
tree passes 9 review groups, 10,632 comparisons and 243 explicit depth-rejection assertions
against the private package. Tar member bytes equal the tested source. Docs-site installation
and 20 normal Vitest regressions pass. Owner restored both frozen trees and reports full local
validation exit 0, including 14 ASGI tests and matching three input hashes. Agent independently
verifies both installed chains and 20 regressions per app; prior install/DNS failures are historical.

Normal Vitest suites in both apps now contain installed-package depth, boundary, original
behavior, source identity and real consumer regressions. Locks are npm-generated and reviewed.
The owner command completes unchanged audits, full make check and the additional ASGI bridge.
The supplied excerpt omits the preceding detailed output; record this as owner-reported local
completion, not agent full-gate or revision-bound CI proof. Existing evidence stays separately labelled.
An artifact version or expected lock preview is not npm-audit proof.

## Consequences and owner responsibilities

The repository owner accepts temporary dependency maintenance. Keep original advisory identity
and base-release provenance explicit. Version-based audit may not classify a private derivative
the same way as its base, so review future upstream braces advisories against the recorded source.
Source identity plus regression tests establish this correction; no audit exception is allowed.
Retire the private package only after a verified official release passes the same tests and audit.

This third-party dependency retains its upstream source and license; the authored patch and
project tests are separately reviewable. Existing third-party parser function sizes are inherited.
The owner reviews this maintenance choice and inherited source structure before adoption.
File/function standards continue to apply to authored project code and tests.

No deployment, route mounting, credentials, provider, publication or product license change is
included. The current bounded window is not automatically extended. PR/CI and any owner-applied
review labels remain separate gates; the agent cannot approve its own work.
