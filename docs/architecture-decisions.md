# Architecture Decision Records (ADRs)

## ADR-001: Supabase PostgreSQL, Auth, and Storage
- **Context:** We need a robust relational database with strong multi-tenant security, user authentication, and object storage for ZIPs.
- **Decision:** Use Supabase as the primary data layer.
- **Consequences:** Provides out-of-the-box Row Level Security (RLS) which is critical for zero-trust tenant isolation. Reduces the need to build custom auth/storage microservices.

## ADR-002: FastAPI Backend
- **Context:** The backend needs to orchestrate asynchronous jobs, handle high concurrency, and provide structured API schemas.
- **Decision:** Use Python with FastAPI and Pydantic.
- **Consequences:** Excellent async support, automatic OpenAPI docs, and native integration with AI/Data-science libraries (Python ecosystem).

## ADR-003: Next.js Frontend
- **Context:** We need a responsive, SEO-friendly, and maintainable frontend framework.
- **Decision:** Use Next.js (React) with Tailwind CSS.
- **Consequences:** Allows for server-side rendering where appropriate and standardizes the UI stack.

## ADR-004: Provider-Agnostic AI Architecture
- **Context:** Relying solely on one LLM provider introduces vendor lock-in and single points of failure.
- **Decision:** Build an abstract `AIProvider` Python interface.
- **Consequences:** We can swap between OpenAI, Anthropic, Gemini, or local models without rewriting the AI Engine's business logic.

## ADR-005: Application Intermediate Representation (AIR)
- **Context:** Feeding raw web source code into an LLM to generate Flutter code is unreliable and prone to hallucination.
- **Decision:** Implement deterministic parsing to generate a JSON-based AIR, which is then fed to the AI.
- **Consequences:** Slower initial analysis phase, but vastly improves the accuracy, security, and reproducibility of the generated Flutter code.

## ADR-006: gVisor / Firecracker Sandbox
- **Context:** Uploaded ZIPs are explicitly hostile and must not be able to compromise the worker node.
- **Decision:** Execute all extraction, analysis, and build steps inside gVisor or Firecracker sandboxes.
- **Consequences:** Increases infrastructure complexity and overhead per job, but is non-negotiable for preventing RCE and tenant data cross-contamination.

## ADR-007: Separate Admin Panel
- **Context:** Mixing admin capabilities into the customer frontend increases the risk of privilege escalation bugs.
- **Decision:** Build a physically separate `admin-panel` application.
- **Consequences:** Admins must log into a different domain. Simplifies frontend security rules.

## ADR-008: Hybrid Cybersecurity Tooling
- **Context:** Building custom SAST engines for JS/TS and Dart is prohibitively expensive.
- **Decision:** Wrap existing tools (Semgrep, Trivy) for standard checks, and build custom parsers only for ForgeFlow-specific migration security logic.
- **Consequences:** Faster time-to-market for security scanning, relies on external tool updates for zero-days.

## ADR-009: Asynchronous Migration Jobs
- **Context:** Generating an entire application takes minutes, far exceeding standard HTTP timeouts.
- **Decision:** Use Redis and background workers (Celery/RQ) to process migrations asynchronously. Clients poll or use WebSockets for updates.
- **Consequences:** Adds operational complexity (Redis, Worker scaling) but ensures reliable long-running tasks.
