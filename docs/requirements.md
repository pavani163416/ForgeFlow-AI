# Product Requirements: ForgeFlow AI

## 1. Product Overview
ForgeFlow AI is a production-grade Software-as-a-Service (SaaS) platform designed to automate the secure conversion of existing web applications into mobile-optimized Flutter applications. The platform leverages deterministic code analysis alongside controlled AI generation to produce secure, high-quality mobile source code.

## 2. Functional Requirements

### 2.1 Ingestion & Analysis
- **F-101 (Secure ZIP Upload):** The system must accept application source code via a ZIP archive.
- **F-102 (Framework Detection):** The system must automatically identify the source framework (initially React + Node.js/Express).
- **F-103 (Deterministic Parsing):** The system must analyze the source AST, routes, dependencies, and component tree deterministically without relying on AI.
- **F-104 (AIR Generation):** The system must output an Application Intermediate Representation (AIR) matching a strict JSON schema.

### 2.2 Security Scanning
- **F-201 (Source Secret Detection):** The system must scan the uploaded web application for hardcoded secrets, API keys, and credentials.
- **F-202 (Dependency Scanning):** The system must identify vulnerable dependencies in the source application's package manifests.
- **F-203 (SAST):** The system must perform Static Application Security Testing on the source code.
- **F-204 (Target Security Scanning):** The system must scan the generated Flutter application to ensure secrets were not copied and no new mobile-specific vulnerabilities (e.g., insecure storage) were introduced.

### 2.3 AI Migration & Generation
- **F-301 (Migration Planning):** The system must use the AIR to generate a structural migration plan mapping web components to Flutter equivalents.
- **F-302 (UI Adaptation):** The AI must adapt web UIs into mobile-native UX paradigms rather than 1:1 desktop web reproductions.
- **F-303 (Code Generation):** The AI must generate strictly typed, compile-ready Flutter Dart source code.

### 2.4 Validation & Remediation
- **F-401 (Automated Build):** The system must compile the generated Flutter code.
- **F-402 (Linting & Static Analysis):** The system must run `flutter analyze` against the generated project.
- **F-403 (AI Remediation):** If the build or security gates fail, the system must trigger a bounded AI remediation loop to correct the code.
- **F-404 (Max Retries):** Remediation loops must abort after a configurable maximum retry limit (default: 3).

### 2.5 Tenancy & Administration
- **F-501 (Multi-Tenancy):** Users must be organized into Organizations with strict boundaries.
- **F-502 (RBAC):** Access control must support Owner, Admin, Member, and Viewer roles.
- **F-503 (Subscription Tiers):** The system must enforce quotas based on Free, Pro, Team, and Enterprise plans.
- **F-504 (Admin Panel):** Platform operators must have a dedicated internal application to monitor jobs, users, and security alerts.

## 3. Non-Functional Requirements (NFR)

### 3.1 Security & Compliance
- **S-101 (Zero-Trust Uploads):** All uploaded ZIPs must be considered hostile and processed in a sandboxed, restricted environment (e.g., gVisor).
- **S-102 (Tenant Isolation):** Data isolation must be enforced at the database level via Supabase Row Level Security (RLS).
- **S-103 (Prompt Injection Resistance):** The AI Engine must sanitize inputs and strictly isolate source code text from system instructions.

### 3.2 Performance & Scalability
- **P-101 (Asynchronous Processing):** Migration jobs must run asynchronously using background worker queues.
- **P-102 (Horizontal Scalability):** The backend, AI Engine, and Cyber Engine must be horizontally scalable.
- **P-103 (Timeouts):** Migration jobs must enforce strict processing time limits (e.g., max 60 minutes).

### 3.3 Reliability & Recoverability
- **R-101 (Job Idempotency):** The migration pipeline state machine must be capable of resuming or cleanly failing if a worker node dies.
- **R-102 (Disaster Recovery):** The platform must support full database point-in-time recovery and artifact restoration.

### 3.4 Observability
- **O-101 (Audit Logging):** All security-sensitive actions and AI remediation attempts must be durably logged.
- **O-102 (Tracing):** Migration jobs must have a unique Correlation ID tracking the request across the Frontend, Backend, AI Engine, and Cyber Engine.
