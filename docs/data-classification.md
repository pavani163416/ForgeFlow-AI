# Data Classification Policy: ForgeFlow AI

This document defines the data classification levels and handling requirements for all data processed by the ForgeFlow AI platform.

## 1. Classification Levels

| Level | Name | Description |
|---|---|---|
| **L4** | **Restricted / Highly Sensitive** | Data that, if exposed, would cause severe financial, reputational, or legal damage to the tenant or ForgeFlow. |
| **L3** | **Confidential** | Proprietary customer data or PII. Not public. Exposure causes moderate harm. |
| **L2** | **Internal** | Operational data, system configurations, and aggregate metrics. Not for public disclosure. |
| **L1** | **Public** | Marketing material, public documentation. Safe for public release. |

## 2. Data Types and Classification

### 2.1 Customer Source Code & Artifacts
- **Classification:** **L4 (Restricted)**
- **Includes:** Uploaded ZIP archives, generated Flutter source code, AIR (Application Intermediate Representation), compiled binaries (APK/AAB).
- **Storage:** Supabase Storage (S3-compatible). Must use Server-Side Encryption (SSE).
- **Access:** Strictly controlled via Supabase RLS policies tied to the Organization ID. Short-lived signed URLs for download.
- **Retention:** Deleted automatically based on subscription tier (e.g., 7 days for Free, 30 days for Pro) or immediately upon user request.

### 2.2 Security Findings & Reports
- **Classification:** **L4 (Restricted)**
- **Includes:** Vulnerability reports, identified secrets, SAST results from the source web app or generated Flutter app.
- **Storage:** PostgreSQL database. Specific sensitive findings (like the exact secret string, if stored at all) must be encrypted at the application layer before DB insertion.
- **Access:** Enforced via RLS. Visible only to Organization Admins/Owners.

### 2.3 User Profile & Authentication Data
- **Classification:** **L3 (Confidential)**
- **Includes:** Email addresses, password hashes, MFA seeds, organization membership.
- **Storage:** Supabase Auth schema.
- **Access:** Platform-managed. Cannot be queried directly by unauthenticated clients.

### 2.4 AI Prompts and Outputs
- **Classification:** **L3 (Confidential)**
- **Includes:** The actual text prompts sent to the LLM and the raw string outputs.
- **Handling:** Secrets must be redacted (L4 -> L3 downgrade) *before* inclusion in prompts. Prompts may be logged for debugging/quality purposes but are subject to strict retention (e.g., 14 days) and restricted internal access.

### 2.5 Audit Logs and System Events
- **Classification:** **L2 (Internal)**
- **Includes:** Login events, API request IDs, job state transitions, subscription changes.
- **Storage:** Immutable audit tables.
- **Access:** Visible to ForgeFlow Platform Admins via the internal Admin Panel. Customers can view logs strictly scoped to their Organization.

## 3. Data Deletion (Right to be Forgotten)

When a customer deletes a Project or their entire Organization:
1. All L4 data (Source ZIPs, Artifacts, Security Findings, AIR) is immediately soft-deleted and permanently destroyed within 24 hours.
2. Background workers run a cascade deletion across Supabase Storage and PostgreSQL.
3. Relevant L3 data (AI prompt logs containing source code snippets) expires organically based on the short-retention policy (max 14 days).
