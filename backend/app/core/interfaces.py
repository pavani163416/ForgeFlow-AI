from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

# --- Storage ---

class StorageProvider(ABC):
    @abstractmethod
    async def upload(self, bucket: str, path: str, file_content: bytes) -> str:
        pass

    @abstractmethod
    async def download(self, bucket: str, path: str) -> bytes:
        pass

    @abstractmethod
    async def delete(self, bucket: str, path: str) -> bool:
        pass

    @abstractmethod
    async def generate_access_url(self, bucket: str, path: str, expires_in: int = 3600) -> str:
        """Generate a signed URL for secure download/upload."""
        pass


# --- Sandbox ---

class SandboxExecutionResult(BaseModel):
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool

class SandboxProvider(ABC):
    @abstractmethod
    async def create(self, image: str, resources: Dict[str, Any]) -> str:
        """Create a sandbox and return its ID. Implementation uses Docker + gVisor."""
        pass

    @abstractmethod
    async def execute(self, sandbox_id: str, command: List[str], timeout: int = 600) -> SandboxExecutionResult:
        """Execute a command securely inside the sandbox."""
        pass

    @abstractmethod
    async def collect_artifacts(self, sandbox_id: str, internal_path: str, external_path: str) -> bool:
        """Retrieve output files from the sandbox workspace."""
        pass

    @abstractmethod
    async def terminate(self, sandbox_id: str) -> bool:
        """Destroy the sandbox and clean up resources."""
        pass


# --- AI Engine ---

class AIProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str, **kwargs) -> str:
        pass

    @abstractmethod
    async def structured_generate(self, prompt: str, system_prompt: str, schema: Any, **kwargs) -> Any:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass


# --- Security Engine ---

class SecurityFindingModel(BaseModel):
    severity: str
    category: str
    title: str
    description: str
    location: Optional[str]

class SecurityScanner(ABC):
    @abstractmethod
    async def scan_source(self, project_path: str) -> List[SecurityFindingModel]:
        pass

    @abstractmethod
    async def scan_dependencies(self, project_path: str) -> List[SecurityFindingModel]:
        pass

    @abstractmethod
    async def scan_generated_code(self, project_path: str) -> List[SecurityFindingModel]:
        pass


# --- Message Queue ---

class JobQueue(ABC):
    @abstractmethod
    async def enqueue(self, queue_name: str, payload: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    async def dequeue(self, queue_name: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def acknowledge(self, queue_name: str, job_id: str) -> bool:
        pass

    @abstractmethod
    async def dead_letter(self, queue_name: str, job_id: str, reason: str) -> bool:
        pass
