# Deployment Architecture: ForgeFlow AI

## 1. Cloud Provider & Infrastructure

ForgeFlow AI is designed to be cloud-agnostic at the application layer, but the Sandbox requirements dictate specific infrastructure choices for the worker nodes.

- **Primary Cloud:** AWS or Google Cloud Platform (GCP).
- **Orchestration:** Kubernetes (EKS / GKE) for high availability and rolling updates.
- **Database & Storage:** Supabase (managed cloud offering or self-hosted on VMs depending on data residency requirements).
- **Cache & Queue:** Redis (ElastiCache / Cloud Memorystore).

## 2. Service Deployment Strategies

### 2.1 Frontend & Admin Panel (Next.js)
- Deployed via Vercel or as standard Docker containers in Kubernetes (Node.js runtime).
- Scaled horizontally based on incoming HTTP traffic.
- Behind a CDN (Cloudflare/CloudFront) for static asset caching and edge protection.

### 2.2 Backend (FastAPI)
- Deployed as Docker containers in Kubernetes.
- Scaled horizontally based on CPU utilization and HTTP request queue depth.
- Stateless (all state is in Supabase/Redis).

### 2.3 Worker Nodes & Sandbox Environment
This is the most complex deployment tier due to the need for nested virtualization or specialized runtimes.
- **Option A (AWS):** EC2 instances running Firecracker microVMs. The Python Worker process runs on the host EC2 instance and spawns a new Firecracker microVM for each migration job.
- **Option B (GCP):** GKE using gVisor (`runsc`) as the container runtime. The Worker pod spawns sibling pods/containers using the gVisor runtime class to isolate the extraction and analysis phases.

### 2.4 Internal Engines (AI & Cyber)
- Deployed as standard Kubernetes deployments.
- Exposed only internally via Kubernetes ClusterIP services.
- The Cyber Engine includes bundled binaries (Semgrep, Trivy) in its container image.

## 3. CI/CD Pipeline

We utilize GitHub Actions for continuous integration and continuous deployment.

1. **Lint & Test:** On PR creation, run `flake8`, `mypy`, `eslint`, and Pytest/Jest suites.
2. **Security Scanning:** Run `trivy` on Dockerfiles and `semgrep` on source code.
3. **Build Images:** On merge to `main`, build Docker images and push to the Container Registry (ECR/GCR).
4. **Deploy to Staging:** Automatically deploy to the Staging Kubernetes cluster using ArgoCD or Helm.
5. **E2E Tests:** Run end-to-end Cypress/Playwright tests against Staging.
6. **Production:** Manual approval triggers the Helm release to the Production cluster.

## 4. Secret Management

- Kubernetes `ExternalSecrets` operator syncs secrets from AWS Secrets Manager / GCP Secret Manager into Kubernetes Secrets.
- Pods mount these secrets as environment variables.
- Supabase JWT secrets, Database connection strings, and AI Provider API keys are never stored in plain text.
