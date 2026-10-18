# Sandboxed dev image: the project toolchain + a default-deny egress firewall
# (init-firewall.sh). See docs/decisions/0004.
#
# The tag is `3.12-bookworm`, not `1-3.12-bookworm`: with the leading image-version segment,
# Dependabot parses 3.12 → 3.13 as a PATCH bump, so the minor-version ignore rule in
# .github/dependabot.yml never applied (#19). The Python version must match CI and the backend
# image — tests/guards/test_runtime_alignment.py checks.
FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm@sha256:edf22d42b215ab03876d5523aff0e31a0e0c69afb9bd05bc4e2724b2af697a65

# Firewall tooling. iptables/ipset apply the policy at container start (needs NET_ADMIN).
# Reviewed exception (ADR-0018, 2026-09-24): hadolint DL3008 asks for pinned apt versions. This
# is a dev-only image whose base is pinned by digest; Debian drops superseded package versions
# from its mirrors, so exact apt pins here would break the build on the next point release
# without adding meaningful assurance. The shipped images install no apt packages.
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
        iptables ipset dnsutils jq \
    && rm -rf /var/lib/apt/lists/*

COPY init-firewall.sh /usr/local/bin/init-firewall.sh
RUN chmod +x /usr/local/bin/init-firewall.sh \
    && echo 'vscode ALL=(root) NOPASSWD: /usr/local/bin/init-firewall.sh' \
       > /etc/sudoers.d/init-firewall
