# The PostgreSQL the backend test suite runs against (TA-015, ADR-0016): the same major version
# as deploy/docker-compose.yml, pinned by digest so every run tests the same bytes.
#
# This file is never built. backend/tests/conftest.py reads the FROM line below and runs the
# image as it is. It lives in a Dockerfile only so that Dependabot refreshes the digest (after
# the same 7-day cooldown as every other image) and hadolint lints it. A new PostgreSQL major
# version is a deliberate PR, taken together with production, never a weekly bump.
FROM postgres:17-alpine@sha256:b0f9560a2de083e2cc7382e75f808c7381a32852a7ec49117deedb300e552b24
