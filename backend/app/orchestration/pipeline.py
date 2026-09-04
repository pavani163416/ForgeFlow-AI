import json
from app.core.state_machine import MigrationState, validate_transition
from app.core.logger import get_logger
from app.core.audit import log_audit_event
from app.analysis.analyzer import DeterministicAnalyzer
from app.security.engine import SecurityEngine
from app.planning.planner import MigrationPlanner
from app.air.serializer import AIRSerializer
from app.core.interfaces import StorageProvider

logger = get_logger(__name__)

class OrchestrationPipeline:
    """
    Manages the phase 3 pipeline execution safely and idempotently.
    ANALYZING -> SECURITY_SCANNING -> AIR_GENERATION -> PLANNING
    """
    def __init__(self, organization_id: str, project_id: str, migration_id: str, storage: StorageProvider):
        self.organization_id = organization_id
        self.project_id = project_id
        self.migration_id = migration_id
        self.storage = storage
        self.bucket = "migrations"

    async def run_analysis_stage(self, source_dir: str):
        # State: QUEUED -> ANALYZING (transition happens in worker before calling this)
        logger.info(f"Starting Analysis for {self.migration_id}")
        
        try:
            # 1. Deterministic Analysis
            analyzer = DeterministicAnalyzer(source_dir)
            air = analyzer.analyze()
            
            # 2. Serialize and Store AIR
            air_json = AIRSerializer.serialize(air)
            path = f"{self.organization_id}/{self.project_id}/{self.migration_id}/air.json"
            
            await self.storage.upload(self.bucket, path, air_json.encode('utf-8'), self.organization_id)
            
            log_audit_event("ANALYSIS_COMPLETED", "migration", self.organization_id, self.migration_id)
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            log_audit_event("ANALYSIS_FAILED", "migration", self.organization_id, self.migration_id, metadata={"error": str(e)})
            raise

    async def run_security_stage(self, source_dir: str):
        # State: ANALYZING -> SECURITY_SCANNING
        logger.info(f"Starting Security Scanning for {self.migration_id}")
        
        try:
            engine = SecurityEngine(self.organization_id, self.project_id, self.migration_id, "1.0")
            findings = engine.scan(source_dir)
            
            findings_dict = [f.model_dump(mode='json') for f in findings]
            path = f"{self.organization_id}/{self.project_id}/{self.migration_id}/security_findings.json"
            
            await self.storage.upload(self.bucket, path, json.dumps(findings_dict, indent=2).encode('utf-8'), self.organization_id)
            
            log_audit_event("SECURITY_SCAN_COMPLETED", "migration", self.organization_id, self.migration_id)
        except Exception as e:
            logger.error(f"Security scan failed: {str(e)}")
            log_audit_event("SECURITY_SCAN_FAILED", "migration", self.organization_id, self.migration_id, metadata={"error": str(e)})
            raise

    async def run_planning_stage(self):
        # State: SECURITY_SCANNING -> PLANNING
        logger.info(f"Starting Planning for {self.migration_id}")
        
        try:
            # Load AIR
            air_path = f"{self.organization_id}/{self.project_id}/{self.migration_id}/air.json"
            air_data = await self.storage.download(self.bucket, air_path, self.organization_id)
            air = AIRSerializer.deserialize(air_data.decode('utf-8'))
            
            # Load Findings
            findings_path = f"{self.organization_id}/{self.project_id}/{self.migration_id}/security_findings.json"
            findings_data = await self.storage.download(self.bucket, findings_path, self.organization_id)
            findings = json.loads(findings_data.decode('utf-8'))
            
            planner = MigrationPlanner(air, []) 
            plan = planner.generate_plan()
            
            plan_path = f"{self.organization_id}/{self.project_id}/{self.migration_id}/migration_plan.json"
            await self.storage.upload(self.bucket, plan_path, plan.model_dump_json(indent=2).encode('utf-8'), self.organization_id)
            
            log_audit_event("PLANNING_COMPLETED", "migration", self.organization_id, self.migration_id)
        except Exception as e:
            logger.error(f"Planning failed: {str(e)}")
            log_audit_event("PLANNING_FAILED", "migration", self.organization_id, self.migration_id, metadata={"error": str(e)})
            raise
