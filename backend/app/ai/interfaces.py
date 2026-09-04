from typing import Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod

class AIProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system: Optional[str] = None) -> Tuple[str, Dict[str, int]]:
        """
        Returns text output and token usage dictionary:
        {'input_tokens': int, 'output_tokens': int, 'total_tokens': int}
        """
        pass

    @abstractmethod
    async def structured_generate(self, prompt: str, schema: Dict[str, Any], system: Optional[str] = None) -> Tuple[Dict[str, Any], Dict[str, int]]:
        """
        Returns structured output and token usage dictionary.
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass
