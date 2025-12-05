from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class BaseAgent(ABC):
    """
    Abstract base class for all AI Agents.
    Enforces a standard interface regardless of the underlying provider.
    """
    
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Standard text generation."""
        pass
    
    @abstractmethod
    def search(self, query: str) -> Optional[str]:
        """Generation with web search capabilities."""
        pass
