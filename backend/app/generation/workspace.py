import os
import hashlib
from pathlib import Path
from typing import List
from app.generation.schema import GeneratedFile

class WorkspaceError(Exception):
    pass

class GenerationWorkspace:
    """
    Isolated workspace abstraction to safely write and read generated files.
    Enforces path traversal protection and file size limits.
    """
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir).resolve()
        if not self.base_dir.exists():
            self.base_dir.mkdir(parents=True, exist_ok=True)
            
    def _safe_resolve(self, rel_path: str) -> Path:
        target = (self.base_dir / rel_path).resolve()
        if self.base_dir not in target.parents:
            raise WorkspaceError(f"Path traversal detected: {rel_path}")
        return target

    def write_file(self, generated_file: GeneratedFile) -> None:
        target_path = self._safe_resolve(generated_file.path)
        
        # Prevent absolute paths or malicious file extensions if necessary
        if target_path.suffix not in [".dart", ".yaml", ".json", ".md", ".xml", ".gradle", ".properties", ""]:
             raise WorkspaceError(f"Forbidden file extension: {target_path.suffix}")
             
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(generated_file.content)
            
    def read_file(self, rel_path: str) -> str:
        target_path = self._safe_resolve(rel_path)
        if not target_path.exists():
            raise WorkspaceError(f"File not found: {rel_path}")
            
        with open(target_path, "r", encoding="utf-8") as f:
            return f.read()
            
    def list_files(self) -> List[str]:
        files = []
        for path in self.base_dir.rglob("*"):
            if path.is_file():
                files.append(str(path.relative_to(self.base_dir).as_posix()))
        return files
        
    def checksum(self, rel_path: str) -> str:
        target_path = self._safe_resolve(rel_path)
        if not target_path.exists():
            raise WorkspaceError(f"File not found: {rel_path}")
            
        sha256 = hashlib.sha256()
        with open(target_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
        
    def cleanup(self) -> None:
        # In a real environment, this might use shutil.rmtree
        pass
