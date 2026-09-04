from abc import ABC, abstractmethod
from typing import Dict, Optional
from pydantic import BaseModel

class SandboxResult(BaseModel):
    status: str # "SUCCESS", "FAILURE", "TIMEOUT", "NOT_AVAILABLE"
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    command: str

class SandboxProvider(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def execute(self, workspace_dir: str, command: str, timeout_seconds: int = 300) -> SandboxResult:
        pass
