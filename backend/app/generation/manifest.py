from typing import List, Dict
from pydantic import BaseModel, Field

class FileManifestEntry(BaseModel):
    path: str
    checksum: str
    generation_run_id: str

class GenerationManifest(BaseModel):
    project_id: str
    migration_id: str
    generation_spec_version: str
    air_version: str
    migration_plan_version: str
    flutter_version: str
    dart_version: str
    generator_version: str = "1.0"
    
    files: List[FileManifestEntry] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    generation_runs: List[str] = Field(default_factory=list)
    validation_runs: List[str] = Field(default_factory=list)
