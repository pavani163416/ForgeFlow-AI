-- Add columns for business idempotency
ALTER TABLE generation_runs ADD COLUMN generation_stage TEXT NOT NULL DEFAULT 'initial';
ALTER TABLE generation_runs ADD COLUMN input_identity TEXT NOT NULL DEFAULT 'unknown';

-- Create a unique constraint for business idempotency
ALTER TABLE generation_runs
ADD CONSTRAINT unique_logical_generation
UNIQUE (organization_id, migration_job_id, generation_stage, generation_spec_version, input_identity);
