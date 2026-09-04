import pytest
from app.validation.engine import SchemaValidator, PolicyValidator, ValidationEngine
from app.air.schema import Route
from pydantic import BaseModel

class DummyAIOutput(BaseModel):
    widget_name: str
    code: str

def test_ai_output_schema_validation():
    validator = SchemaValidator(DummyAIOutput)
    
    valid_json = '{"widget_name": "Button", "code": "Container()"}'
    result = validator.validate(valid_json)
    assert result.is_valid is True
    
    invalid_json = '{"code": "Container()"}' # Missing widget_name
    result = validator.validate(invalid_json)
    assert result.is_valid is False
    assert len(result.errors) > 0

def test_ai_output_policy_validation():
    validator = PolicyValidator()
    
    valid_code = "Container(child: Text('Hello'))"
    assert validator.validate(valid_code).is_valid is True
    
    # Mocking a policy violation where a raw API Key was generated
    invalid_code = "const apiKey = 'API_KEY_12345';"
    assert validator.validate(invalid_code).is_valid is False
    
def test_validation_pipeline():
    engine = ValidationEngine([
        SchemaValidator(DummyAIOutput),
        PolicyValidator()
    ])
    
    assert engine.run_pipeline('{"widget_name": "Test", "code": "OK"}').is_valid is True
