# Observability Architecture: ForgeFlow AI

## 1. Logging Strategy

All services must implement structured logging (JSON format) to allow ingestion into centralized logging systems (e.g., Datadog, ELK, GCP Cloud Logging).

### 1.1 Context Propagation
Every log entry related to a user request or background job must include:
- `trace_id`: Unique ID for the entire request lifecycle.
- `organization_id`: UUID of the tenant.
- `user_id`: UUID of the user triggering the action (if applicable).
- `migration_job_id`: UUID of the specific migration (if applicable).

### 1.2 Sensitive Data Redaction
**NEVER LOG:**
- Plaintext passwords or JWTs.
- API keys (Customer or Internal).
- Customer Source Code snippets (unless explicitly flagged for L3 storage, securely).
- PII (Email addresses should be masked or omitted in standard application logs).

## 2. Metrics and Telemetry

Services must expose Prometheus-compatible `/metrics` endpoints.

### 2.1 Backend API Metrics
- Request rate (`req/sec`).
- Error rate (`HTTP 4xx`, `HTTP 5xx`).
- Latency (p50, p90, p99).

### 2.2 Worker Metrics
- Queue depth (number of jobs waiting).
- Job duration (time from `QUEUED` to `COMPLETED`/`FAILED`).
- Sandbox provisioning time.
- Task failure rates.

### 2.3 AI Engine Metrics
- Token usage (`prompt_tokens`, `completion_tokens`) aggregated by `organization_id` and `model`.
- AI Provider latency.
- Remediation loop frequency (how often generated code fails compilation).
- Prompt injection detection rate.

## 3. Distributed Tracing

Implement OpenTelemetry (OTel) across all Python (FastAPI/Celery) and TypeScript (Next.js) services to trace requests as they cross network boundaries.

## 4. Alerting and Paging

Alerts are routed to PagerDuty/Slack based on severity.
- **CRITICAL:** High 5xx error rate, Redis queue backup > 1000, AI Provider outage, Sandbox escape detected.
- **WARNING:** Elevated migration failure rate, approaching token quota limits, high memory pressure on worker nodes.
