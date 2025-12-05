from .providers import DashScopeAgent, DeepSeekAgent, KimiAgent

class AgentFactory:
    @staticmethod
    def create(agent_type: str):
        if agent_type.lower() == "architect" or agent_type.lower() == "qwen":
            return DashScopeAgent("Qwen", "Architect", "qwen-max")
        elif agent_type.lower() == "hunter" or agent_type.lower() == "deepseek":
            return DeepSeekAgent("DeepSeek", "Hunter", "deepseek-r1")
        elif agent_type.lower() == "researcher" or agent_type.lower() == "kimi":
            return KimiAgent("Kimi", "Researcher", "Moonshot-Kimi-K2-Instruct")
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
