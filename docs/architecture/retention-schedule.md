# Retention Schedule

| | |
|---|---|
| Version | 1.0 (draft for counsel review) |
| Date | 23 September 2026 |
| Defined by | [Addendum 03](addendum-03-operations-data-security-mobile.md) D-22 |

Periods below are Accord's proposed defaults. **Counsel must confirm them** against the Philippine Data Privacy Act, GDPR and target-market law before launch.

A **legal hold** always overrides deletion, lifecycle transitions and crypto-shredding until it is released by an audited, dual-approved action.

## Deletion methods

| Method | Meaning |
|---|---|
| **Never** | Kept permanently. It must contain no readable personal data (Addendum 03 §5.2) |
| **Hard delete** | Object and rows removed. Backups age out on their own schedule |
| **Crypto-shred** | The encryption key or salt is destroyed. Ciphertext and commitments stay but are unreadable |
| **Anonymize** | Personal fields replaced by an "erased person" marker. The structure is kept for integrity and statistics |
| **Automatic** | Enforced by the storage platform's lifecycle or log-bucket retention |

## Schedule

| Data class | Where | Default | Tenant can change | Deletion method | Basis |
|---|---|---|---|---|---|
| Signed manifests, envelopes | Cell and `public-projections` | Permanent | No | **Never** (personal data outside the hash) | The record's integrity is the product |
| Transparency log, checkpoints, OpenTimestamps proofs, witness co-signatures | Trust `log-tiles`, `anchors` | Permanent | No | **Never** | Public verifiability |
| Personal-data layer (names, contacts, salts) | Control, per-person key | Life of account + erasure on request | No (the person can) | **Crypto-shred** | Consent or contract; erasure right |
| Passkey key bindings | Control and log | Permanent (public keys only) | No | Never (no personal data beyond `person_id`) | Signature verifiability |
| Decisions, appeals, case records | Cell | 10 years after case final | Longer only | **Anonymize** | Recourse; legal claims |
| Domain audit events | Cell (`audit`) | 7 years | Longer only | **Anonymize** | Accountability; legal claims |
| Tenant artifacts | Cell `artifacts` | Tenant-defined (default: life of project + 1 year) | Yes | **Hard delete** | Contract |
| Restricted evidence | Cell `evidence-restricted` | Life of claim or case + tenant-defined period | Yes (within range) | **Crypto-shred** (tenant key) | Contract; legal claims |
| Sealed evidence | Cell `evidence-sealed` | Case final + tenant-defined period (default 2 years) | Yes (within range) | **Crypto-shred** | Contract; legal claims |
| Content fingerprints | Cell and control (public only) | Same as the source artifact or record | Follows source | Hard delete with source | Contract |
| Notifications and delivery evidence | Cell | 3 years | Longer only | **Anonymize** | Proof of notice |
| AI working data (prompts, intermediate outputs) | Intelligence scratch | 30 days | Shorter only | **Hard delete** | Purpose limitation |
| AI evaluation sets | Nonprod | Until superseded | — | Hard delete | Consented or synthetic only |
| Uploads in quarantine | `uploads-quarantine` | 7 days | No | **Automatic** | Security |
| Exports | `exports` | 7 days | No | **Automatic** | Purpose limitation |
| Application logs | Cloud Logging `_Default` | 30 days | No | **Automatic** | Operations |
| Security logs | Security bucket plus `security-archive` | 1 year | No | **Automatic** | Security; incident response |
| GCP audit logs | `_Required` plus archive | 400 days, then archive to 1 year total | No | **Automatic** | Security; compliance |
| Identity data (accounts, sessions, MFA) | Zynth | Per Zynth retention settings; erasure through Zynth data-subject requests | — | Zynth (audit chain retained) | Contract |
| Database backups (Accord, Zynth) | Cloud SQL, `backups` | 35 days (point-in-time recovery 7 days) | No | **Automatic** | Recovery |
| Billing records | Paddle and Accord `billing` | 10 years | No | Hard delete after period | Tax and accounting law (confirm) |
| Closed tenant | All cell data | 30-day grace, then deletion per class above | — | Per class; public records stay, anonymized | Contract end |

## Procedures

- **Personal erasure:**
  1. Verify the requester's identity.
  2. Check for legal holds or legal obligations.
  3. Crypto-shred the personal-data layer.
  4. Anonymize records.
  5. Request Zynth erasure.
  6. Confirm to the person within the statutory period.
- **Tenant offboarding:** export offered, then a 30-day grace period, then deletion per class. Signed public records remain, with personal data erased where requested.
- **Changes to this schedule:** by ADR, with counsel sign-off. Tenant settings can only move within the allowed range.
