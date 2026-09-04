# API Specification: ForgeFlow AI

This outlines the RESTful API contracts implemented by the FastAPI Backend. All endpoints (except webhooks) require a valid Supabase JWT Bearer token.

## 1. Projects API

### `POST /api/v1/projects`
- **Desc:** Create a new project workspace.
- **Auth:** Member/Admin/Owner.
- **Req:** `{ "name": "MyApp", "organization_id": "uuid" }`
- **Res:** `201 Created` `{ "id": "uuid", "name": "MyApp" }`

### `POST /api/v1/projects/{project_id}/migrations`
- **Desc:** Initialize a new migration job. Enforces subscription limits.
- **Auth:** Member/Admin/Owner.
- **Res:** `201 Created` `{ "job_id": "uuid", "upload_url": "https://<supabase-signed-put-url>" }`
- **Note:** The client uploads the ZIP directly to Supabase Storage using the signed URL, bypassing the backend to save bandwidth.

## 2. Migrations API

### `POST /api/v1/migrations/{job_id}/start`
- **Desc:** Triggers the pipeline after the ZIP is successfully uploaded to Storage.
- **Auth:** Member/Admin/Owner.
- **Action:** Changes job status to `QUEUED` and pushes task to Redis.
- **Res:** `202 Accepted`

### `GET /api/v1/migrations/{job_id}`
- **Desc:** Get current job status, stage, and duration.
- **Auth:** Viewer/Member/Admin/Owner.
- **Res:** `200 OK` `{ "status": "GENERATING", "progress": 45, "current_step": "Generating Screen: Dashboard" }`

### `POST /api/v1/migrations/{job_id}/cancel`
- **Desc:** Safely aborts a running migration.
- **Auth:** Admin/Owner.

## 3. Artifacts & Security API

### `GET /api/v1/migrations/{job_id}/artifacts`
- **Desc:** List generated artifacts (Source ZIP, APK, Reports).
- **Auth:** Viewer/Member/Admin/Owner.
- **Res:** `200 OK` `[{ "type": "FLUTTER_SOURCE", "download_url": "https://<signed-get-url>" }]`

### `GET /api/v1/migrations/{job_id}/security`
- **Desc:** Retrieve security findings for a job.
- **Auth:** Viewer/Member/Admin/Owner.
- **Res:** `200 OK` `{ "critical": 0, "high": 1, "findings": [...] }`

## 4. Internal Service Contracts (gRPC / REST)

*Note: These are internal APIs, not exposed to the public.*

### Backend -> AI Engine
- `POST /internal/ai/plan` (Payload: AIR JSON -> Returns: Migration Plan JSON)
- `POST /internal/ai/generate` (Payload: Component JSON + AIR Context -> Returns: Dart Source Code)

### Backend -> Cybersecurity Engine
- `POST /internal/cyber/scan` (Payload: Sandbox Path -> Returns: Findings JSON)
