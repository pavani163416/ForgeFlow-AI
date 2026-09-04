from typing import List, Optional
from app.generation.schema import GenerationSpec, GeneratedFile
from app.generation.generator import FlutterGenerator
from app.generation.workspace import GenerationWorkspace

class GenerationOrchestrator:
    """
    Drives the generation process based strictly on the GenerationSpec.
    Ensures that the AI generator only builds the requested components in order.
    """
    def __init__(self, generator: FlutterGenerator, workspace: GenerationWorkspace):
        self.generator = generator
        self.workspace = workspace
        
    def run_generation(self, spec: GenerationSpec, run_id: str) -> List[GeneratedFile]:
        """
        Executes the staged generation pipeline.
        Models -> Services -> Navigation -> Screens
        """
        all_files: List[GeneratedFile] = []
        
        # 1. Base project structure (pubspec, etc.)
        base = self.generator.generate_module("base", spec, all_files)
        self._commit_files(base)
        all_files.extend(base)
        
        # 2. Models
        models = self.generator.generate_module("models", spec, all_files)
        self._commit_files(models)
        all_files.extend(models)
        
        # 3. Services
        services = self.generator.generate_module("services", spec, all_files)
        self._commit_files(services)
        all_files.extend(services)
        
        # 4. Screens
        screens = self.generator.generate_module("screens", spec, all_files)
        self._commit_files(screens)
        all_files.extend(screens)
        
        return all_files
        
    def _commit_files(self, files: List[GeneratedFile]):
        for f in files:
            self.workspace.write_file(f)
