# Private braces depth backport

This is Gen6th Accord's private derivative, version 3.0.4-accord.1. It is not an
official micromatch/braces release and is not intended for registry publication.

Base: braces 3.0.3, upstream commit 74b2db2938fad48a2ea54a9c8bf27a37a62c350d.
Original index.js, lib/utils.js and the MIT LICENSE are retained unchanged.
The five-file depth patch has SHA-256:
a3f08706e45f1e180112f91f07a871b284b92613bccdfb2724a165ff4f96c91e.

The patch bounds parser and direct-AST recursion at 100, permits stricter limits,
normalizes finite limits to nonnegative integers, and preserves published
stringify parent behavior. Unreleased upstream parser changes are excluded.
fill-range is pinned to the already installed 7.1.1; no lifecycle scripts exist.

Retire this derivative when a verified upstream release passes the regression
and consumer checks. Keeping the original package name preserves advisory
identity; version metadata does not by itself prove the source is corrected.
