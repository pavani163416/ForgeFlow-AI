# Migration Pipeline State Machine

Every migration in ForgeFlow AI is explicitly modeled as a state machine. This ensures that failures are handled gracefully, jobs can be resumed if a worker dies, and the UI can accurately reflect progress.

## 1. Valid States

| State | Description | Transition Trigger |
|---|---|---|
| `CREATED` | Initial record created in DB. | Client calls `POST /projects/{id}/migrations` |
| `UPLOADING` | Client is uploading ZIP to Supabase Storage. | (Client-side tracking) |
| `UPLOADED` | Client completed upload. | Client calls `POST /migrations/{id}/start` |
| `QUEUED` | Job pushed to Redis queue. | Backend acknowledges start request. |
| `ANALYZING` | Worker extracting and parsing source code. | Worker picks up job from queue. |
| `SECURITY_SCANNING`| Cyber Engine scanning web source. | `ANALYZING` completes successfully. |
| `AIR_GENERATION` | Deterministic extraction of the AIR. | `SECURITY_SCANNING` completes. |
| `PLANNING` | AI Engine designing Flutter architecture. | `AIR_GENERATION` completes. |
| `GENERATING` | AI Engine writing Dart code. | `PLANNING` completes. |
| `REVIEWING` | AI static review of generated code. | `GENERATING` completes. |
| `VALIDATING` | Worker running `flutter analyze`/tests. | `REVIEWING` completes. |
| `BUILDING` | Worker running `flutter build apk`. | `VALIDATING` completes successfully. |
| `REMEDIATING` | AI attempting to fix a build/validation error. | `VALIDATING` or `BUILDING` fails. |
| `FINAL_SECURITY_SCAN`| Cyber Engine scanning generated Flutter. | `BUILDING` completes successfully. |
| `COMPLETED` | Migration successful, artifacts saved. | `FINAL_SECURITY_SCAN` passes. |
| `FAILED` | Terminal failure state (e.g., max retries hit). | Unrecoverable error or max retries. |
| `CANCELLED` | User requested abort. | Client calls `POST /migrations/{id}/cancel` |

## 2. Hard Limits & Failure Handling

Every job enforces the following constraints:
- `MAX_RUNTIME`: Hard timeout for the entire job (e.g., 60 minutes). If exceeded, the worker kills the sandbox and transitions state to `FAILED`.
- `MAX_RETRIES`: During the `REMEDIATING` loop, if the AI cannot fix a compile error after N attempts, the job is marked `FAILED`.
- `MAX_AI_COST`: If a specific job exceeds its allocated token budget, generation halts.

## 3. Worker Node Failure (Idempotency)

If a Worker node crashes (e.g., OOM kill by Kubernetes) while a job is in the `GENERATING` state:
- The Redis visibility timeout expires.
- Another Worker picks up the job.
- The new Worker checks the database, sees the job was in `GENERATING`, and can resume from the last saved state (e.g., skipping `ANALYZING` and `AIR_GENERATION` if those artifacts were already persisted to Supabase Storage).
