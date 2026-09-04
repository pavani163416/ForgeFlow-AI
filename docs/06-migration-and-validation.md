# 06. Migration and Validation (Phase 3 Implemented)

## Overview
This document describes the orchestration of the migration pipeline and the strict validation foundation enforcing security over untrusted AI outputs.

## Status
**IMPLEMENTED**
- Migration Planner (`MigrationPlanner`) deriving mobile architecture
- `ValidationEngine` pipeline enforcing strict Pydantic schema validation
- `OrchestrationPipeline` driving the `ANALYZING` -> `SECURITY_SCANNING` -> `PLANNING` sequence

**PARTIALLY IMPLEMENTED**
- `PolicyValidator` and `SecurityValidator` logic (Interfaces implemented, deep security rules pending Phase 4).

## Migration Planner
The Migration Planner receives the generated AIR and Security Findings. It is responsible for architecting the target mobile application structure. 
- It maps web `Routes` to mobile `Screens`.
- It maps `APIEndpoints` to structured Flutter `Services`.
- It explicitly flags unsupported functionality (e.g. Cookie-based auth) requiring manual actions rather than hallucinating secure behavior.

## Orchestration Pipeline
The pipeline operates strictly within the boundaries of the State Machine.
1. **QUEUED -> ANALYZING**: Run deterministic AST parsing and persist `air.json`.
2. **ANALYZING -> SECURITY_SCANNING**: Orchestrate static scanners and persist `security_findings.json`.
3. **SECURITY_SCANNING -> PLANNING**: Analyze AIR and Findings, generating `migration_plan.json`.

All stages use deterministic database/storage persistence to guarantee recoverability.

## Validation Foundation
The Validation Engine treats all AI output as explicitly untrusted. Outputs must pass a strict sequence of validators before being accepted:
1. `SchemaValidator` (JSON compliance and structural enforcement)
2. `SemanticValidator` (Logical coherence)
3. `SecurityValidator` (Absence of malicious payloads)
4. `PolicyValidator` (Absence of sensitive data exposure)

## Phase 4 Hardening Status
- Dependency Validation: IMPLEMENTED
- Artifact Packaging & Immutability: IMPLEMENTED
- Idempotency & State Machine: IMPLEMENTED
