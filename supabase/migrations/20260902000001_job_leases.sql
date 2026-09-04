-- Add worker leasing columns to migration_jobs to support idempotency and reliability

ALTER TABLE migration_jobs
ADD COLUMN worker_id TEXT,
ADD COLUMN lease_expires_at TIMESTAMPTZ,
ADD COLUMN heartbeat_at TIMESTAMPTZ;

-- Ensure that these new columns are accessible if any specific RLS was filtering them (not applicable here, but good practice).
