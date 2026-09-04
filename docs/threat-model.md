# Threat Model: ForgeFlow AI

This document outlines the threat model for ForgeFlow AI using the STRIDE methodology (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege).

## 1. Hostile Uploads & Archive Processing

The most critical entry point for attacks is the ZIP archive upload feature.

| Threat | STRIDE | Mitigation |
|---|---|---|
| **Archive Bomb / Zip Bomb** | DoS | Implement strict limits on compressed and uncompressed sizes (e.g., max 100MB compressed, max 500MB uncompressed). Abort extraction if limits are exceeded. |
| **Path Traversal** | Tampering, Info Disclosure | Validate all file paths during extraction. Reject any files containing `../` or attempting to write outside the designated sandbox workspace. |
| **Malicious Symlinks** | Info Disclosure, Privilege Elevation | Disable symlink resolution during extraction, or validate that symlinks only point to files within the extracted workspace. |
| **Malware Execution** | Elevation of Privilege | Extract and analyze archives *only* inside a heavily restricted gVisor/Firecracker sandbox. No arbitrary scripts (e.g., `npm install`, `postinstall` hooks) from the uploaded archive are executed unless explicitly required and heavily contained. |

## 2. AI Threats

| Threat | STRIDE | Mitigation |
|---|---|---|
| **Prompt Injection** | Tampering, Info Disclosure | Source code is passed to the AI Engine as *data*, clearly separated from system instructions using strict prompt templates (e.g., XML tags). The LLM is instructed to ignore any instructions embedded within the source code. |
| **Data Exfiltration via AI** | Info Disclosure | The AI Provider has no access to internal networks. The generated output is strictly parsed and validated against a schema. Secrets discovered in the source code are redacted *before* the code is sent to the AI Provider. |
| **Cross-Tenant Context Leakage** | Info Disclosure | Each migration job instantiates a fresh context. RAG (Retrieval-Augmented Generation) databases (if used) enforce tenant ID filtering on all queries. |

## 3. Multi-Tenant SaaS Threats

| Threat | STRIDE | Mitigation |
|---|---|---|
| **Insecure Direct Object Reference (IDOR)** | Info Disclosure, Tampering | The Backend explicitly validates that the authenticated user belongs to the Organization that owns the requested resource (Project, Migration Job, Artifact) on *every* request. |
| **Tenant Escape via Database** | Elevation of Privilege, Info Disclosure | Supabase Row Level Security (RLS) is enabled on all tables. A user physically cannot query data outside their organization, even if an API endpoint has an authorization logic flaw. |
| **Subscription Bypass** | Spoofing, DoS | The Backend acts as the strict enforcer of all limits (concurrent migrations, total migrations, AI token limits). The Frontend's UI state is purely cosmetic regarding limits. |

## 4. Infrastructure & Internal Threats

| Threat | STRIDE | Mitigation |
|---|---|---|
| **Worker Compromise** | Elevation of Privilege | Workers operate with least privilege. They do not hold the Supabase Service Role key. They authenticate to the database via short-lived, scoped credentials or API endpoints. |
| **Sandbox Escape** | Elevation of Privilege | Use gVisor (runsc) or Firecracker microVMs. Linux capabilities are dropped. The root filesystem is read-only. Network egress is blocked (preventing reverse shells). |
| **Repudiation of Actions** | Repudiation | All security-sensitive actions (login, role change, subscription change, migration start/cancel, security policy override) are logged to an immutable `audit_logs` table. |
