# Security Architecture: ForgeFlow AI

## 1. Core Principles

The security architecture of ForgeFlow AI is built upon the following principles:
- **Zero-Trust Input:** All user-provided data, specifically uploaded ZIP archives and source code, are considered explicitly hostile.
- **Defense in Depth:** Multiple layers of security controls protect the application, infrastructure, and tenant data.
- **Tenant Isolation:** Strict cryptographic and logical separation of data across organizations.
- **Least Privilege:** Services, workers, and human operators operate with the minimum permissions required to perform their functions.

## 2. Security Boundaries and Trust Zones

### 2.1 Untrusted Zone (Client)
- **Scope:** The user's browser or API client.
- **Controls:** All input is validated at the edge. The Frontend performs UX-level authorization, but no security decisions rely on it.

### 2.2 DMZ / API Gateway (Backend)
- **Scope:** The FastAPI backend receiving requests from the Frontend/Admin Panel.
- **Controls:** Terminates TLS. Validates JWTs issued by Supabase Auth. Enforces API rate limits, input sanitization, and authorization checks before forwarding tasks to internal services or queues.

### 2.3 Trusted Internal Zone
- **Scope:** Worker nodes, AI Engine, Cyber Engine, Redis queue.
- **Controls:** Accessible only from the Backend. Network policies deny inbound traffic from the public internet. Communication between internal services uses mutual authentication or restricted VPC routing.

### 2.4 High-Risk Execution Zone (Sandbox)
- **Scope:** The environment where user ZIPs are extracted and parsed.
- **Controls:** Ephemeral gVisor or Firecracker microVMs. Network egress is blocked (except to specific required artifact registries, if necessary). Read-only host filesystem. CPU and memory cgroups enforce strict resource limits. Processes run as non-root.

### 2.5 Persistence Zone (Supabase)
- **Scope:** PostgreSQL Database and Object Storage.
- **Controls:** Row Level Security (RLS) ensures that every query is strictly scoped to the authenticated user's organization. Storage buckets have explicit RLS policies for read/write access. Data is encrypted at rest.

## 3. Authentication & Authorization

### 3.1 Identity Provider
- Supabase Auth manages user identities, passwords (hashed via bcrypt/Argon2), and MFA.

### 3.2 Role-Based Access Control (RBAC)
- **Organization Roles:** Owner, Admin, Member, Viewer.
- **Enforcement:** Enforced at the FastAPI API layer via middleware, and at the database layer via RLS policies matching the user's UUID and organization membership.

### 3.3 Service-to-Service Authentication
- Internal services communicate using short-lived JWTs or mutual TLS (mTLS).
- The AI Engine and Cyber Engine do not possess Supabase Service Role keys. Only specific, privileged worker nodes have access to write migration results back to the database.

## 4. Secret Management

- **Infrastructure Secrets:** AI Provider API Keys, Database URLs, and internal HMAC keys are injected via environment variables managed by a secure secret store (e.g., AWS Secrets Manager, HashiCorp Vault). They are never committed to version control.
- **Customer Secrets:** If customers need to provide secrets (e.g., for private package registries), they are encrypted at the API edge using KMS, stored encrypted in the database, and only decrypted inside the ephemeral Sandbox just-in-time for analysis or building.

## 5. Artifact Security

- **Storage:** Uploaded ZIPs and generated artifacts (Flutter source, APKs) are stored in Supabase Storage.
- **Access:** URLs to artifacts are never public. Clients request short-lived, signed URLs via the Backend to download artifacts.
- **Retention:** Artifacts are securely deleted upon tenant request or after the subscription retention period expires.
