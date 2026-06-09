from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass
class PromptTemplate:
    template: str
    required_vars: List[str] = field(default_factory=list)
    default_vars: Dict[str, Any] = field(default_factory=dict)

    def format(self, **kwargs) -> str:
        # Merge defaults and inputs
        merged_vars = {**self.default_vars, **kwargs}
        # Check required variables
        missing = [v for v in self.required_vars if v not in merged_vars]
        if missing:
            raise ValueError(f"Missing required variables for prompt formatting: {missing}")
        return self.template.format(**merged_vars)

@dataclass
class CollectorAgentConfig:
    name: str
    agent_type: str
    prompt_template: PromptTemplate
    target_fields: List[str]
    source_name: str
    search_queries: List[str] = field(default_factory=list)

@dataclass
class CoordinatorConfig:
    name: str
    agent_type: str
    prompt_template: PromptTemplate
    collector_fields: List[str]
    computed_fields: List[str] = field(default_factory=list)
    report_sources: List[str] = field(default_factory=list)

@dataclass
class FactCheckerConfig:
    name: str
    agent_type: str
    prompt_template: PromptTemplate
    verify_fields: List[str]

@dataclass
class UnderwriterConfig:
    name: str
    agent_type: str
    business_rule: str
    prompt_template: PromptTemplate
    input_fields: List[str]
    log_fields: List[str]
    output_fields: List[str] = field(default_factory=list)
    prompt_vars: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BusinessRuleConfig:
    rule_id: str
    rule_name: str
    description: str
    collector_configs: Dict[str, CollectorAgentConfig]
    coordinator_config: CoordinatorConfig
    fact_checker_config: FactCheckerConfig
    underwriter_config: UnderwriterConfig
