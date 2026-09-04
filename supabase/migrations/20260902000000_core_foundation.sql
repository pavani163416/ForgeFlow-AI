-- ForgeFlow AI Core Foundation Schema

-- 1. EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. ENUMS
CREATE TYPE organization_role AS ENUM ('OWNER', 'ADMIN', 'MEMBER', 'VIEWER');
CREATE TYPE subscription_tier AS ENUM ('FREE', 'PRO', 'TEAM', 'ENTERPRISE');
CREATE TYPE subscription_status AS ENUM ('ACTIVE', 'PAST_DUE', 'CANCELED', 'TRIAL');
CREATE TYPE migration_status AS ENUM ('CREATED', 'UPLOADING', 'UPLOADED', 'QUEUED', 'ANALYZING', 'SECURITY_SCANNING', 'AIR_GENERATION', 'PLANNING', 'GENERATING', 'REVIEWING', 'VALIDATING', 'BUILDING', 'REMEDIATING', 'FINAL_SECURITY_SCAN', 'COMPLETED', 'FAILED', 'CANCELLED');
CREATE TYPE artifact_type AS ENUM ('SOURCE_ZIP', 'AIR', 'FLUTTER_SOURCE', 'APK', 'AAB', 'MIGRATION_REPORT', 'SECURITY_REPORT', 'VALIDATION_REPORT', 'BUILD_LOG');
CREATE TYPE finding_severity AS ENUM ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO');
CREATE TYPE scan_stage AS ENUM ('SOURCE_SCAN', 'FLUTTER_SCAN', 'DEPENDENCY_SCAN', 'CONFIG_SCAN');

-- 3. TABLES

-- PROFILES
CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ORGANIZATIONS
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ORGANIZATION MEMBERS
CREATE TABLE organization_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role organization_role NOT NULL DEFAULT 'MEMBER',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(organization_id, user_id)
);

-- SUBSCRIPTIONS
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    tier subscription_tier NOT NULL DEFAULT 'FREE',
    status subscription_status NOT NULL DEFAULT 'ACTIVE',
    billing_provider_id TEXT,
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(organization_id)
);

-- SUBSCRIPTION EVENTS
CREATE TABLE subscription_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- USAGE RECORDS
CREATE TABLE usage_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    metric_name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- PROJECTS
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    framework TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- PROJECT VERSIONS
CREATE TABLE project_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    version_label TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- MIGRATION JOBS
CREATE TABLE migration_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    project_version_id UUID REFERENCES project_versions(id) ON DELETE SET NULL,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    status migration_status NOT NULL DEFAULT 'CREATED',
    retry_count INTEGER NOT NULL DEFAULT 0,
    correlation_id TEXT,
    error_reason TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- MIGRATION STEPS
CREATE TABLE migration_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    migration_job_id UUID NOT NULL REFERENCES migration_jobs(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    step_name TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- MIGRATION LOGS
CREATE TABLE migration_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    migration_job_id UUID NOT NULL REFERENCES migration_jobs(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- MIGRATION ARTIFACTS
CREATE TABLE migration_artifacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    migration_job_id UUID NOT NULL REFERENCES migration_jobs(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    type artifact_type NOT NULL,
    storage_path TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- SECURITY SCANS
CREATE TABLE security_scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    migration_job_id UUID NOT NULL REFERENCES migration_jobs(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    stage scan_stage NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- SECURITY FINDINGS
CREATE TABLE security_findings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    security_scan_id UUID NOT NULL REFERENCES security_scans(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    severity finding_severity NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    location TEXT,
    status TEXT DEFAULT 'OPEN',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- SECURITY REMEDIATIONS
CREATE TABLE security_remediations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    security_finding_id UUID NOT NULL REFERENCES security_findings(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    applied_fix TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- AI RUNS
CREATE TABLE ai_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    migration_job_id UUID NOT NULL REFERENCES migration_jobs(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    request_id TEXT,
    status TEXT,
    latency_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- AI USAGE
CREATE TABLE ai_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ai_run_id UUID NOT NULL REFERENCES ai_runs(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    cost_usd NUMERIC NOT NULL DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- AUDIT LOGS
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    result TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- SYSTEM EVENTS
CREATE TABLE system_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type TEXT NOT NULL,
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. ROW LEVEL SECURITY (RLS)

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE organization_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscription_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE migration_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE migration_steps ENABLE ROW LEVEL SECURITY;
ALTER TABLE migration_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE migration_artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE security_scans ENABLE ROW LEVEL SECURITY;
ALTER TABLE security_findings ENABLE ROW LEVEL SECURITY;
ALTER TABLE security_remediations ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_events ENABLE ROW LEVEL SECURITY;

-- Helper function to check organization membership
CREATE OR REPLACE FUNCTION user_in_org(org_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM organization_members
    WHERE organization_id = org_id AND user_id = auth.uid()
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Profiles: Users can see their own profile
CREATE POLICY "Users can view own profile" ON profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON profiles FOR UPDATE USING (auth.uid() = id);

-- Organizations: Users can view orgs they belong to
CREATE POLICY "Users can view their orgs" ON organizations FOR SELECT USING (user_in_org(id));

-- Organization Members: Users can view members of their orgs
CREATE POLICY "Users can view members of their orgs" ON organization_members FOR SELECT USING (user_in_org(organization_id));

-- Tenant isolated tables policy generation
-- We apply the same policy to all tenant-owned tables
CREATE POLICY "Tenant isolation select" ON subscriptions FOR SELECT USING (user_in_org(organization_id));
CREATE POLICY "Tenant isolation select" ON subscription_events FOR SELECT USING (user_in_org(organization_id));
CREATE POLICY "Tenant isolation select" ON usage_records FOR SELECT USING (user_in_org(organization_id));
CREATE POLICY "Tenant isolation select" ON projects FOR SELECT USING (user_in_org(organization_id));
CREATE POLICY "Tenant isolation select" ON project_versions FOR SELECT USING (EXISTS(SELECT 1 FROM projects WHERE projects.id = project_id AND user_in_org(projects.organization_id)));
CREATE POLICY "Tenant isolation select" ON migration_jobs FOR SELECT USING (user_in_org(organization_id));
CREATE POLICY "Tenant isolation select" ON migration_steps FOR SELECT USING (user_in_org(organization_id));
CREATE POLICY "Tenant isolation select" ON migration_logs FOR SELECT USING (user_in_org(organization_id));
CREATE POLICY "Tenant isolation select" ON migration_artifacts FOR SELECT USING (user_in_org(organization_id));
CREATE POLICY "Tenant isolation select" ON security_scans FOR SELECT USING (user_in_org(organization_id));
CREATE POLICY "Tenant isolation select" ON security_findings FOR SELECT USING (user_in_org(organization_id));
CREATE POLICY "Tenant isolation select" ON security_remediations FOR SELECT USING (user_in_org(organization_id));
CREATE POLICY "Tenant isolation select" ON ai_runs FOR SELECT USING (user_in_org(organization_id));
CREATE POLICY "Tenant isolation select" ON ai_usage FOR SELECT USING (user_in_org(organization_id));
CREATE POLICY "Tenant isolation select" ON audit_logs FOR SELECT USING (user_in_org(organization_id));

CREATE POLICY "No access to system events" ON system_events FOR SELECT USING (FALSE);
