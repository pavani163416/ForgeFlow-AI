# Disaster Recovery & Business Continuity: ForgeFlow AI

## 1. Recovery Objectives
- **Recovery Point Objective (RPO):** 5 minutes for Database (PostgreSQL). 1 hour for Object Storage (Artifacts).
- **Recovery Time Objective (RTO):** 2 hours for full platform restoration in a secondary region.

## 2. Component Strategies

### 2.1 Supabase PostgreSQL
- **Backup Strategy:** Point-in-Time Recovery (PITR) enabled. Continuous WAL archiving to S3. Daily full snapshots.
- **Recovery:** In the event of primary database corruption, a new instance is spun up and restored from the latest WAL logs, minimizing data loss to minutes.

### 2.2 Supabase Storage (Object Storage)
- **Backup Strategy:** Cross-Region Replication (CRR) enabled for the underlying S3 buckets.
- **Recovery:** If the primary region fails, the application is repointed to the replicated bucket in the secondary region.

### 2.3 Redis Queue
- **Backup Strategy:** Redis is treated as ephemeral state for job queuing. No persistent backups are strictly required.
- **Recovery:** If Redis goes down, in-flight jobs will time out. Upon Redis restoration, the Backend can run a reconciliation script against the `migration_jobs` table (finding jobs in `QUEUED`, `ANALYZING`, etc.) and re-enqueue them.

### 2.4 Worker Nodes & Compute
- **Backup Strategy:** Infrastructure as Code (Terraform) and Stateless Containers.
- **Recovery:** A secondary Kubernetes cluster in a different region can be provisioned via Terraform and hydrated with Docker images from the global Container Registry within minutes.

## 3. Migration Job Recovery

Migration jobs are designed to be idempotent and restartable.

### 3.1 Worker Node Crash
If a worker node dies mid-job, the Redis task visibility timeout will expire, and another worker will pick up the job. The worker logic must check Supabase for existing artifacts (e.g., AIR JSON) before re-running expensive steps.

### 3.2 AI Provider Outage
If the primary AI Provider (e.g., OpenAI) goes down, the AI Engine abstraction layer can be configured to fallback to a secondary provider (e.g., Anthropic) seamlessly, preventing a full platform outage.

## 4. Data Deletion in DR
Data deletion requests (Right to be Forgotten) must cascade into backups. A script must exist to prune specific `organization_id` data from daily snapshots if required by compliance (GDPR/CCPA).
