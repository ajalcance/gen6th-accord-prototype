# 0017. Primary GCP region: asia-southeast1 (Singapore)

- **Status:** Accepted
- **Date:** 2026-09-24
- **Deciders:** Albert Alcance (founder)

## Context

Every Accord deployable, both Cloud SQL instances, the storage buckets and the Vertex AI endpoint must live in one primary region. The plan carried "asia-southeast1 assumed" as an open item (Addenda 01–03). The launch is Philippines-first, and the Philippine Data Privacy Act and GDPR-aligned controls apply (v1.0 §15.3). Zynth Auth's managed service already runs in Singapore.

## Decision

1. The primary region for all Accord and self-hosted Zynth resources is **asia-southeast1 (Singapore)**. This covers the prod, trust, identity and nonprod projects.
2. Vertex AI is pinned to asia-southeast1 (Addendum 03 §5.9).
3. Dual-region storage (Addendum 03 §7) and cross-region recovery (Addendum 02 §6.4, Stage C) choose their second location when those stages are built. That choice will be its own ADR.
4. The org policy "allowed regions only" (Addendum 03 §3.1) allows asia-southeast1 now, and the second region once it is decided.

## Consequences

- Lowest latency for Philippine users among Google Cloud regions near the Philippines, with the full service set Accord needs (Cloud Run, Cloud SQL, Cloud KMS, Cloud Tasks, Pub/Sub, Vertex AI). Model availability per region must be checked for each pinned model at Stage 3.
- Data residency is in Singapore. Customer contracts and the privacy notice must state it. Enterprise customers needing another region get a dedicated cell (Addendum 01 D-02).
- Prices are regional. The cost estimates must be confirmed in the GCP pricing calculator for asia-southeast1 before provisioning.

## Alternatives considered

- **A US region** (lower list prices for some services). Rejected: higher latency for the Philippines-first audience, and weaker residency alignment with Asian customers.
- **asia-east1 (Taiwan) or asia-northeast1 (Tokyo).** Rejected: no advantage over Singapore for the Philippines, and Singapore matches Zynth's managed region.
