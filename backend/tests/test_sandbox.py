import pytest
import os
from app.sandbox.docker_gvisor import DockerGVisorSandboxProvider
from app.validation.flutter import FlutterExecutionValidator

def test_sandbox_not_available_skip():
    # In CI without Docker, sandbox should correctly identify as unavailable
    sandbox = DockerGVisorSandboxProvider()
    
    # Let's mock _check_availability to ensure it returns False
    sandbox._available = False
    
    validator = FlutterExecutionValidator(sandbox, "/tmp/workspace")
    result = validator.validate({})
    
    assert result.is_valid is False
    assert "Sandbox execution = NOT AVAILABLE" in result.errors[0]

def test_sandbox_execute_degrades():
    sandbox = DockerGVisorSandboxProvider()
    sandbox._available = False
    
    res = sandbox.execute("/tmp/workspace", "flutter test")
    assert res.status == "NOT_AVAILABLE"
    assert "not available" in res.stderr
