from typing import Type, Any
from src.registry import BusinessRuleRegistry
from src.config import BusinessRuleConfig

class TokenUsageTracker:
    def __init__(self):
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0

    def add_usage(self, prompt_tokens: int, completion_tokens: int) -> None:
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_tokens += (prompt_tokens + completion_tokens)

    def get_summary(self) -> dict:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens
        }

class AgentFactory:
    def __init__(self, config: BusinessRuleConfig):
        self.config = config
        self.tracker = TokenUsageTracker()

    @classmethod
    def for_rule(cls, rule_id: str) -> "AgentFactory":
        config = BusinessRuleRegistry.get(rule_id)
        return cls(config)

    def create_collector_agent(self, agent_type: str, agent_class: Type) -> Any:
        if agent_type not in self.config.collector_configs:
            raise ValueError(f"Collector '{agent_type}' is not configured for rule '{self.config.rule_id}'")
        col_config = self.config.collector_configs[agent_type]
        return agent_class(col_config, tracker=self.tracker)

    def create_coordinator(self, agent_class: Type) -> Any:
        return agent_class(self.config.coordinator_config, tracker=self.tracker)

    def create_fact_checker(self, agent_class: Type) -> Any:
        return agent_class(self.config.fact_checker_config, tracker=self.tracker)

    def create_underwriter(self, agent_class: Type) -> Any:
        return agent_class(self.config.underwriter_config, tracker=self.tracker)
