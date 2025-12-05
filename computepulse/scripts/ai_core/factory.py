from .base_agent import BaseAgent
from .providers import DashScopeAgent, DeepSeekAgent, KimiAgent, GLMAgent

class AgentFactory:
    @staticmethod
    def create(provider_type: str, **kwargs) -> BaseAgent:
        p_type = provider_type.lower()
        if p_type == "qwen":
            return DashScopeAgent("Qwen", "Architect", **kwargs)
        elif p_type == "deepseek":
            return DeepSeekAgent("DeepSeek", "Hunter", **kwargs)
        elif p_type == "kimi":
            return KimiAgent("Kimi", "Researcher", **kwargs)
        elif p_type == "glm":
            return GLMAgent("GLM", "Analyst", **kwargs)
        else:
            raise ValueError(f"Unknown provider: {provider_type}")
