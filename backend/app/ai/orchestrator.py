import uuid
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from .interfaces import AIProvider
from app.security.redaction import SecretRedactor

class AILimitExceededException(Exception):
    pass

class PromptInjectionDetectedException(Exception):
    pass

class AIOrchestrator:
    """
    Manages AI execution with strict limits, redacting secrets,
    and enforcing context isolation.
    """
    def __init__(self, provider: AIProvider, max_tokens: int = 4000, max_retries: int = 3, timeout_seconds: int = 60):
        self.provider = provider
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds

    def _isolate_context(self, system_policy: str, trusted_metadata: str, customer_source: str) -> str:
        """
        Creates a clear boundary between instructions and untrusted customer source.
        """
        redacted_source = SecretRedactor.redact(customer_source)
        
        # Simple injection detection heuristics
        if "ignore all previous instructions" in redacted_source.lower():
            raise PromptInjectionDetectedException("Potential prompt injection detected in customer source.")

        return f"""=== SYSTEM POLICY ===
{system_policy}

=== TRUSTED METADATA ===
{trusted_metadata}

=== CUSTOMER SOURCE (UNTRUSTED) ===
{redacted_source}
"""

    async def generate_with_limits(self, system_policy: str, trusted_metadata: str, customer_source: str) -> Dict[str, Any]:
        """
        Orchestrates an AI call, enforces limits, returns output + audit info.
        """
        safe_prompt = self._isolate_context(system_policy, trusted_metadata, customer_source)
        
        # Enforce timeout
        try:
            result, usage = await asyncio.wait_for(
                self.provider.generate(prompt=safe_prompt, system=system_policy),
                timeout=self.timeout_seconds
            )
        except asyncio.TimeoutError:
            raise AILimitExceededException("AI Provider execution exceeded maximum duration.")
            
        if usage.get("total_tokens", 0) > self.max_tokens:
            raise AILimitExceededException(f"Token limit exceeded: {usage.get('total_tokens')} > {self.max_tokens}")

        # Construct audit payload
        audit_record = {
            "request_id": str(uuid.uuid4()),
            "provider": self.provider.__class__.__name__,
            "operation": "generate",
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "status": "success",
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        return {
            "result": result,
            "audit": audit_record
        }
