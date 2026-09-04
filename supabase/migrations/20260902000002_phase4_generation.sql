-- ForgeFlow AI Phase 4: Controlled Flutter Generation
-- New Schema Additions

-- 1. TABLES

-- GENERATION RUNS
CREATE TABLE generation_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    migration_job_id UUID NOT NULL REFERENCES migration_jobs(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    generation_spec_version TEXT,
    flutter_version TEXT,
    dart_version TEXT,
    manifest_checksum TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- GENERATION FILES (Provenance Tracking)
CREATE TABLE generation_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    generation_run_id UUID NOT NULL REFERENCES generation_runs(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    checksum TEXT NOT NULL,
    language TEXT,
    purpose TEXT,
    generation_stage TEXT,
    validation_status TEXT,
    source_references JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- GENERATION REVIEWS (AI Output Advisory Review)
CREATE TABLE generation_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    generation_run_id UUID NOT NULL REFERENCES generation_runs(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    findings JSONB,
    missing_requirements JSONB,
    security_concerns JSONB,
    confidence NUMERIC,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- VALIDATION RUNS (Deterministic Validators)
CREATE TABLE validation_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    generation_run_id UUID NOT NULL REFERENCES generation_runs(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    validator_name TEXT NOT NULL, -- e.g., FileValidator, DependencyValidator, APIContractValidator, FlutterStructureValidator
    status TEXT NOT NULL,
    findings JSONB,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- BUILD RUNS (Sandbox Execution)
CREATE TABLE build_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    generation_run_id UUID NOT NULL REFERENCES generation_runs(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    sandbox_provider TEXT NOT NULL, -- e.g., DockerGVisorSandboxProvider
    status TEXT NOT NULL,
    stdout_summary TEXT,
    stderr_summary TEXT,
    exit_code INTEGER,
    command TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- REMEDIATION RUNS (Patch-based remediation loop)
CREATE TABLE remediation_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    generation_run_id UUID NOT NULL REFERENCES generation_runs(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL,
    status TEXT NOT NULL,
    affected_files JSONB,
    validation_findings JSONB,
    patch_summary TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- 3. ROW LEVEL SECURITY (RLS)
ALTER TABLE generation_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE generation_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE generation_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE validation_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE build_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE remediation_runs ENABLE ROW LEVEL SECURITY;

-- Tenant isolated tables policy generation
CREATE POLICY "Tenant isolation select" ON generation_runs FOR SELECT USING (user_in_org(organization_id));
CREATE POLICY "Tenant isolation select" ON generation_files FOR SELECT USING (user_in_org(organization_id));
CREATE POLICY "Tenant isolation select" ON generation_reviews FOR SELECT USING (user_in_org(organization_id));
CREATE POLICY "Tenant isolation select" ON validation_runs FOR SELECT USING (user_in_org(organization_id));
CREATE POLICY "Tenant isolation select" ON build_runs FOR SELECT USING (user_in_org(organization_id));
CREATE POLICY "Tenant isolation select" ON remediation_runs FOR SELECT USING (user_in_org(organization_id));

CREATE POLICY "Tenant isolation insert" ON generation_runs FOR INSERT WITH CHECK (user_in_org(organization_id));
CREATE POLICY "Tenant isolation update" ON generation_runs FOR UPDATE USING (user_in_org(organization_id));
CREATE POLICY "Tenant isolation delete" ON generation_runs FOR DELETE USING (user_in_org(organization_id));

CREATE POLICY "Tenant isolation insert" ON generation_files FOR INSERT WITH CHECK (user_in_org(organization_id));
CREATE POLICY "Tenant isolation update" ON generation_files FOR UPDATE USING (user_in_org(organization_id));
CREATE POLICY "Tenant isolation delete" ON generation_files FOR DELETE USING (user_in_org(organization_id));

CREATE POLICY "Tenant isolation insert" ON generation_reviews FOR INSERT WITH CHECK (user_in_org(organization_id));
CREATE POLICY "Tenant isolation update" ON generation_reviews FOR UPDATE USING (user_in_org(organization_id));
CREATE POLICY "Tenant isolation delete" ON generation_reviews FOR DELETE USING (user_in_org(organization_id));

CREATE POLICY "Tenant isolation insert" ON validation_runs FOR INSERT WITH CHECK (user_in_org(organization_id));
CREATE POLICY "Tenant isolation update" ON validation_runs FOR UPDATE USING (user_in_org(organization_id));
CREATE POLICY "Tenant isolation delete" ON validation_runs FOR DELETE USING (user_in_org(organization_id));

CREATE POLICY "Tenant isolation insert" ON build_runs FOR INSERT WITH CHECK (user_in_org(organization_id));
CREATE POLICY "Tenant isolation update" ON build_runs FOR UPDATE USING (user_in_org(organization_id));
CREATE POLICY "Tenant isolation delete" ON build_runs FOR DELETE USING (user_in_org(organization_id));

CREATE POLICY "Tenant isolation insert" ON remediation_runs FOR INSERT WITH CHECK (user_in_org(organization_id));
CREATE POLICY "Tenant isolation update" ON remediation_runs FOR UPDATE USING (user_in_org(organization_id));
CREATE POLICY "Tenant isolation delete" ON remediation_runs FOR DELETE USING (user_in_org(organization_id));
