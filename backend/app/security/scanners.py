import os
import re
import uuid
import json
from typing import List
from .models import SecurityFinding
from .redaction import SecretRedactor

class BaseScanner:
    def __init__(self, organization_id: str, project_id: str, migration_id: str, source_version: str):
        self.organization_id = organization_id
        self.project_id = project_id
        self.migration_id = migration_id
        self.source_version = source_version

    def _create_finding(self, rule_id: str, category: str, severity: str, title: str, description: str, 
                        file: str, line: int, evidence: str, recommendation: str, confidence: str = "HIGH") -> SecurityFinding:
        return SecurityFinding(
            finding_id=str(uuid.uuid4()),
            organization_id=self.organization_id,
            project_id=self.project_id,
            migration_id=self.migration_id,
            source_version=self.source_version,
            scanner=self.__class__.__name__,
            rule_id=rule_id,
            category=category,
            severity=severity,
            title=title,
            description=description,
            file=file,
            line=line,
            redacted_evidence=SecretRedactor.redact(evidence),
            recommendation=recommendation,
            confidence=confidence
        )
    
    def scan(self, source_dir: str) -> List[SecurityFinding]:
        raise NotImplementedError

class DependencyScanner(BaseScanner):
    def scan(self, source_dir: str) -> List[SecurityFinding]:
        findings = []
        # Attempt to read package.json
        pkg_json_path = os.path.join(source_dir, "package.json")
        if os.path.exists(pkg_json_path):
            # Since vulnerability DB is not available in phase 3 foundation, we inventory and report UNKNOWN status
            # unless a dependency is explicitly known to be heavily discouraged/blocked
            try:
                with open(pkg_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    deps = data.get("dependencies", {})
                    deps.update(data.get("devDependencies", {}))
                    
                    for dep, version in deps.items():
                        findings.append(self._create_finding(
                            rule_id="dependency_vulnerability_unknown",
                            category="Dependencies",
                            severity="INFO",
                            title=f"Dependency {dep} version {version}",
                            description=f"Vulnerability status UNKNOWN for {dep}@{version} due to missing DB.",
                            file="package.json",
                            line=1,
                            evidence=f'"{dep}": "{version}"',
                            recommendation="Ensure dependency is manually verified.",
                            confidence="HIGH"
                        ))
            except Exception:
                pass
        return findings

class StaticAnalyzer(BaseScanner):
    def scan(self, source_dir: str) -> List[SecurityFinding]:
        findings = []
        patterns = {
            "eval_usage": (re.compile(r'\beval\s*\('), "CRITICAL", "Dangerous eval() usage detected", "Avoid executing dynamic code."),
            "exec_usage": (re.compile(r'\bexec\s*\('), "CRITICAL", "Dangerous exec() usage detected", "Avoid executing dynamic code."),
            "subprocess_usage": (re.compile(r'(child_process\.exec|child_process\.spawn)'), "HIGH", "Subprocess execution detected", "Ensure OS commands are not constructed from user input."),
        }
        
        for root, _, files in os.walk(source_dir):
            for file in files:
                if file.endswith((".js", ".ts", ".py")):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, source_dir)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            for line_no, line in enumerate(f, 1):
                                for rule_id, (pattern, sev, title, rec) in patterns.items():
                                    if pattern.search(line):
                                        findings.append(self._create_finding(
                                            rule_id=rule_id, category="Static Analysis", severity=sev,
                                            title=title, description=title, file=rel_path, line=line_no,
                                            evidence=line.strip(), recommendation=rec
                                        ))
                    except Exception:
                        continue
        return findings

class ConfigurationAnalyzer(BaseScanner):
    def scan(self, source_dir: str) -> List[SecurityFinding]:
        findings = []
        patterns = {
            "debug_mode": (re.compile(r'(DEBUG\s*=\s*true|DEBUG\s*=\s*1|DEBUG\s*=\s*\'true\')', re.IGNORECASE), "MEDIUM", "Debug Mode Enabled", "Disable debug mode in production.", "MEDIUM"),
            "http_endpoint": (re.compile(r'http://'), "HIGH", "Insecure HTTP URL Detected", "Use HTTPS for all external communication.", "MEDIUM")
        }
        
        for root, _, files in os.walk(source_dir):
            for file in files:
                if file.endswith((".env", ".json", ".js", ".ts", ".yaml", ".yml")):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, source_dir)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            for line_no, line in enumerate(f, 1):
                                for rule_id, (pattern, sev, title, rec, conf) in patterns.items():
                                    if pattern.search(line) and "http://localhost" not in line:
                                        findings.append(self._create_finding(
                                            rule_id=rule_id, category="Configuration", severity=sev,
                                            title=title, description=title, file=rel_path, line=line_no,
                                            evidence=line.strip(), recommendation=rec, confidence=conf
                                        ))
                    except Exception:
                        continue
        return findings

class AuthAnalyzer(BaseScanner):
    def scan(self, source_dir: str) -> List[SecurityFinding]:
        findings = []
        # Look for typical auth middleware logic
        auth_detected = False
        for root, _, files in os.walk(source_dir):
            for file in files:
                if file.endswith((".js", ".ts", ".py")):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if re.search(r'(passport\.|jwt\.verify|session\(|app\.use\(auth)', content, re.IGNORECASE):
                                auth_detected = True
                    except Exception:
                        continue
                        
        if not auth_detected:
             findings.append(self._create_finding(
                rule_id="missing_auth_middleware",
                category="Authentication",
                severity="HIGH",
                title="Missing Authentication Middleware",
                description="No common authentication middleware (like JWT or Passport) was detected statically.",
                file="global",
                line=0,
                evidence="N/A",
                recommendation="Ensure routes are protected and authorization logic exists.",
                confidence="LOW"
            ))
        return findings
