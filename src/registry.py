from typing import Dict, List
from src.config import BusinessRuleConfig

class BusinessRuleRegistry:
    _registry: Dict[str, BusinessRuleConfig] = {}

    @classmethod
    def register(cls, config: BusinessRuleConfig) -> None:
        cls._registry[config.rule_id] = config

    @classmethod
    def get(cls, rule_id: str) -> BusinessRuleConfig:
        if rule_id not in cls._registry:
            raise ValueError(f"Rule with id '{rule_id}' is not registered.")
        return cls._registry[rule_id]

    @classmethod
    def list_rules(cls) -> List[str]:
        return list(cls._registry.keys())
