import uuid
from typing import List
from .models import SecurityFinding
from .redaction import SecretRedactor
from .scanners import DependencyScanner, StaticAnalyzer, ConfigurationAnalyzer, AuthAnalyzer

class SecurityEngine:
    def __init__(self, organization_id: str, project_id: str, migration_id: str, source_version: str):
        self.organization_id = organization_id
        self.project_id = project_id
        self.migration_id = migration_id
        self.source_version = source_version
        
    def scan(self, source_dir: str) -> List[SecurityFinding]:
        """
        Orchestrates all security scanners.
        """
        findings = []
        
        # 1. Secret Scanner (Still inline for now, uses Redactor)
        findings.extend(self._run_secret_scanner(source_dir))
        
        # 2. Dependency Scanner
        dep_scanner = DependencyScanner(self.organization_id, self.project_id, self.migration_id, self.source_version)
        findings.extend(dep_scanner.scan(source_dir))
        
        # 3. Static Analyzer
        static_analyzer = StaticAnalyzer(self.organization_id, self.project_id, self.migration_id, self.source_version)
        findings.extend(static_analyzer.scan(source_dir))
        
        # 4. Configuration Analyzer
        config_analyzer = ConfigurationAnalyzer(self.organization_id, self.project_id, self.migration_id, self.source_version)
        findings.extend(config_analyzer.scan(source_dir))
        
        # 5. Auth Analyzer
        auth_analyzer = AuthAnalyzer(self.organization_id, self.project_id, self.migration_id, self.source_version)
        findings.extend(auth_analyzer.scan(source_dir))
        
        return findings
        
    def _run_secret_scanner(self, source_dir: str) -> List[SecurityFinding]:
        # Basic stub for secret scanner, using redaction to prove concept
        finding = SecurityFinding(
            finding_id=str(uuid.uuid4()),
            organization_id=self.organization_id,
            project_id=self.project_id,
            migration_id=self.migration_id,
            source_version=self.source_version,
            scanner="SecretScanner",
            rule_id="hardcoded_secret",
            category="Secrets",
            severity="CRITICAL",
            title="Hardcoded API Key Detected",
            description="A hardcoded API key was found in the source code.",
            file="config.js",
            line=10,
            redacted_evidence=SecretRedactor.redact("const API_KEY = 'sk_live_1234567890';"),
            recommendation="Move to environment variables.",
            confidence="HIGH"
        )
        return [finding]
