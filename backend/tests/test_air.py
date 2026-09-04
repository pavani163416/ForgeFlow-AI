import pytest
import json
from app.air.schema import AIR, Route, APIEndpoint, Provenance
from app.air.serializer import AIRSerializer

def test_air_schema_serialization():
    air = AIR(
        source_version="v1",
        framework="React",
        language="TypeScript",
        routes=[
            Route(path="/", component_id="Home", provenance=Provenance(confidence="HIGH", detection_method="manual")),
            Route(path="/about", component_id="About", provenance=Provenance(confidence="HIGH", detection_method="manual"))
        ]
    )
    
    serialized = AIRSerializer.serialize(air)
    data = json.loads(serialized)
    
    assert data["air_version"] == "1.0"
    assert data["framework"] == "React"
    assert len(data["routes"]) == 2
    
def test_air_determinism():
    air1 = AIR(
        source_version="v1", framework="React", language="TypeScript",
        routes=[Route(path="/", component_id="Home", provenance=Provenance(confidence="HIGH", detection_method="manual"))]
    )
    air2 = AIR(
        source_version="v1", framework="React", language="TypeScript",
        routes=[Route(path="/", component_id="Home", provenance=Provenance(confidence="HIGH", detection_method="manual"))]
    )
    
    # Even if they are different objects, serialization with sorted keys guarantees identical strings
    assert AIRSerializer.serialize(air1) == AIRSerializer.serialize(air2)
