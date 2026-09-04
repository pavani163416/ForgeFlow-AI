import json
from .schema import AIR

class AIRSerializer:
    @staticmethod
    def serialize(air: AIR) -> str:
        """
        Serializes the AIR model to a deterministic JSON string.
        Pydantic's model_dump_json(exclude_none=True) gets us part way there, 
        but we also sort keys to ensure exact determinism for diffing and hashing.
        """
        # Convert to dict excluding None
        data_dict = air.model_dump(exclude_none=True)
        # Serialize to JSON with sorted keys for determinism
        return json.dumps(data_dict, sort_keys=True, separators=(',', ':'))

    @staticmethod
    def deserialize(air_json: str) -> AIR:
        """
        Deserializes a deterministic JSON string back to an AIR model.
        """
        return AIR.model_validate_json(air_json)
