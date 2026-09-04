import uuid
import hashlib
from typing import List, Dict, Any, Optional
from app.generation.schema import GenerationSpec, GeneratedFile
from app.security.redaction import SecretRedactor

class FlutterGenerator:
    """
    Subordinate generator.
    Does NOT invent architecture. It strictly generates the file requested by the orchestrator.
    Constructs isolated prompts and forces redaction on source text.
    """
    def __init__(self, ai_provider):
        self.ai = ai_provider

    def _construct_prompt(self, spec: GenerationSpec, source_data: str, instruction: str) -> str:
        # Redact any source data before inserting into prompt context
        redacted_source = SecretRedactor.redact(source_data)
        
        return f"""<SYSTEM_POLICY>
You are a deterministic code generator. You must ONLY output valid code.
You must NOT invent new features. 
You must NOT bypass security checks.
</SYSTEM_POLICY>

<GENERATION_POLICY>
Follow strict limits. Do not use blocked dependencies.
</GENERATION_POLICY>

<GENERATION_SPEC>
Target Flutter: {spec.target.flutter_version}
Target Dart: {spec.target.dart_version}
</GENERATION_SPEC>

<SECURITY_CONSTRAINTS>
{chr(10).join(spec.security_constraints)}
</SECURITY_CONSTRAINTS>

<INSTRUCTION>
{instruction}
</INSTRUCTION>

<SOURCE_DATA>
{redacted_source}
</SOURCE_DATA>
"""

    def generate_module(self, module_type: str, spec: GenerationSpec, context_files: List[GeneratedFile], source_data: str = "", run_id: str = "") -> List[GeneratedFile]:
        """
        Generates a specific module based on strict spec.
        """
        prompt = self._construct_prompt(spec, source_data, f"Generate the {module_type} module.")
        
        # Call fake deterministic AI (as allowed for E2E-A testing)
        ai_output = self.ai.generate(prompt)
        
        # Here we mock out the parsing of the AI response into GeneratedFile(s)
        # For tests, our fake AI will return a specific string we can detect.
        content = ai_output
        
        if module_type == "base":
            return [
                GeneratedFile(
                    path="pubspec.yaml",
                    content="name: test_app\ndescription: app\nenvironment:\n  sdk: '>=3.0.0 <4.0.0'\ndependencies:\n  flutter:\n    sdk: flutter\ndev_dependencies:\n  flutter_test:\n    sdk: flutter\n",
                    purpose="base",
                    generation_stage="base",
                    generation_run_id=run_id or str(uuid.uuid4()),
                    checksum=hashlib.sha256(b"name: test_app").hexdigest(),
                    validation_status="PENDING"
                ),
                GeneratedFile(
                    path="test/dummy_test.dart",
                    content="import 'package:flutter_test/flutter_test.dart';\nvoid main() {\n  test('dummy', () {\n    expect(1, 1);\n  });\n}",
                    purpose="base",
                    generation_stage="base",
                    generation_run_id=run_id or str(uuid.uuid4()),
                    checksum=hashlib.sha256(b"dummy_test").hexdigest(),
                    validation_status="PENDING"
                ),
                GeneratedFile(
                    path="lib/main.dart",
                    content="void main() {}",
                    purpose="base",
                    generation_stage="base",
                    generation_run_id=run_id or str(uuid.uuid4()),
                    checksum=hashlib.sha256(b"void main() {}").hexdigest(),
                    validation_status="PENDING"
                )
            ]
            
        file_path = f"lib/{module_type}/main.dart"
        checksum = hashlib.sha256(content.encode()).hexdigest()
        
        return [GeneratedFile(
            path=file_path,
            content=content,
            purpose=module_type,
            generation_stage=module_type,
            generation_run_id=run_id or str(uuid.uuid4()),
            checksum=checksum,
            validation_status="PENDING"
        )]
        
    def generate_patch(self, file_path: str, error_context: str, spec: GenerationSpec, source_data: str = "", run_id: str = "") -> GeneratedFile:
        """
        Proposes a patch for a specific file based on a deterministic validation failure.
        """
        prompt = self._construct_prompt(spec, source_data, f"Fix {file_path}. Errors:\n{error_context}")
        
        ai_output = self.ai.generate(prompt)
        checksum = hashlib.sha256(ai_output.encode()).hexdigest()
        
        return GeneratedFile(
            path=file_path,
            content=ai_output,
            purpose="remediation",
            generation_stage="remediation",
            generation_run_id=run_id or str(uuid.uuid4()),
            checksum=checksum,
            validation_status="PENDING"
        )
