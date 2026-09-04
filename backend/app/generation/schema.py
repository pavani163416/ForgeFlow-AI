from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class GenerationTarget(BaseModel):
    platform: str = "flutter"
    flutter_version: str
    dart_version: str

class GenerationPolicy(BaseModel):
    max_files: int = 100
    max_file_size_bytes: int = 500000 # 500KB per file limit
    max_project_size_bytes: int = 50000000 # 50MB
    max_generation_steps: int = 50
    max_ai_calls: int = 100
    max_tokens: int = 1000000
    timeout_seconds: int = 1800
    allowed_dependencies: List[str] = Field(default_factory=list)
    blocked_dependencies: List[str] = Field(default_factory=list)
    allowed_file_extensions: List[str] = Field(default_factory=lambda: [".dart", ".yaml", ".json", ".md"])
    forbidden_patterns: List[str] = Field(default_factory=lambda: ["..", "/etc/", "eval("])

class GenerationSpec(BaseModel):
    schema_version: str = "1.0"
    source_project_id: str
    source_version_id: str
    air_version: str
    plan_version: str
    target: GenerationTarget
    security_constraints: List[str] = Field(default_factory=list)
    generation_limits: GenerationPolicy = Field(default_factory=GenerationPolicy)
    # The actual components to generate are derived from the MigrationPlan
    screens: List[str] = Field(default_factory=list)
    navigation: List[str] = Field(default_factory=list)
    services: List[str] = Field(default_factory=list)
    models: List[str] = Field(default_factory=list)

class GeneratedFile(BaseModel):
    path: str
    content: str
    language: str = "dart"
    purpose: str
    source_references: List[str] = Field(default_factory=list)
    generation_stage: str
    generation_run_id: str
    checksum: str
    validation_status: str = "PENDING"
