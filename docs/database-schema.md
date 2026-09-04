# Database Schema: ForgeFlow AI

This document outlines the core Supabase PostgreSQL schema. All tables utilize UUID primary keys and enforce Row Level Security (RLS).

## 1. Core Tenancy Tables

### `organizations`
- `id` (UUID, PK)
- `name` (String)
- `subscription_tier` (Enum: FREE, PRO, TEAM, ENTERPRISE)
- `created_at` (Timestamp)

### `organization_members`
- `id` (UUID, PK)
- `organization_id` (UUID, FK -> organizations.id)
- `user_id` (UUID, FK -> auth.users.id)
- `role` (Enum: OWNER, ADMIN, MEMBER, VIEWER)

**RLS Policy:** Users can only query `organizations` where their `auth.uid()` has an entry in `organization_members`.

## 2. Migration Core

### `projects`
- `id` (UUID, PK)
- `organization_id` (UUID, FK -> organizations.id)
- `name` (String)
- `framework` (String)
- `created_at` (Timestamp)

### `migration_jobs`
- `id` (UUID, PK)
- `project_id` (UUID, FK -> projects.id)
- `status` (Enum: CREATED, UPLOADING, QUEUED, ANALYZING, SECURITY_SCANNING, AIR_GENERATION, PLANNING, GENERATING, REVIEWING, VALIDATING, BUILDING, REMEDIATING, COMPLETED, FAILED, CANCELLED)
- `source_zip_path` (String) - Path in Supabase Storage
- `target_flutter_path` (String) - Path in Supabase Storage
- `started_at` (Timestamp)
- `completed_at` (Timestamp)

### `migration_artifacts`
- `id` (UUID, PK)
- `migration_job_id` (UUID, FK -> migration_jobs.id)
- `type` (Enum: AIR_JSON, MIGRATION_PLAN, FLUTTER_SOURCE, APK, SECURITY_REPORT)
- `storage_path` (String)

**RLS Policy:** Users can only query `projects` and `migration_jobs` where `organization_id` matches their membership.

## 3. Security and Auditing

### `security_findings`
- `id` (UUID, PK)
- `migration_job_id` (UUID, FK -> migration_jobs.id)
- `stage` (Enum: SOURCE_SCAN, FLUTTER_SCAN)
- `severity` (Enum: CRITICAL, HIGH, MEDIUM, LOW, INFO)
- `category` (String) - e.g., "Hardcoded Secret", "Insecure Network"
- `description` (Text)
- `file_path` (String)
- `line_number` (Integer)

### `audit_logs`
- `id` (UUID, PK)
- `organization_id` (UUID, FK -> organizations.id)
- `user_id` (UUID, FK -> auth.users.id)
- `action` (String) - e.g., "MIGRATION_STARTED", "SUBSCRIPTION_CHANGED"
- `metadata` (JSONB)
- `created_at` (Timestamp)

## 4. AI Telemetry

### `ai_usage`
- `id` (UUID, PK)
- `organization_id` (UUID, FK -> organizations.id)
- `migration_job_id` (UUID, FK -> migration_jobs.id)
- `provider` (String)
- `model` (String)
- `prompt_tokens` (Integer)
- `completion_tokens` (Integer)
- `cost_estimate_usd` (Decimal)
- `created_at` (Timestamp)
