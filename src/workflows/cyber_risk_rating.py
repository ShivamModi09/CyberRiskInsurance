from typing import Dict, Any, List, Annotated
from typing_extensions import TypedDict
import operator

from langgraph.graph import START, END, StateGraph
from langgraph.types import RetryPolicy

from src.factory import AgentFactory
from src.collectors import (
    WikipediaCollectorAgent,
    WikidataCollectorAgent,
    SECCollectorAgent,
    DNBCollectorAgent,
    DomainScraperCollectorAgent,
    ResponsesAPICollectorAgent
)
from src.processors import (
    CollectionCoordinatorAgent,
    FactCheckerAgent,
    UnderwriterAgent
)
from src.supervisor import supervisor_node
from src.cache import CachingCollectorWrapper, get_cache_manager

# Reducer to merge reports dictionary
def merge_reports(left: dict, right: dict) -> dict:
    return {**left, **right}

class CyberRiskRatingState(TypedDict, total=False):
    # Inputs
    company_name: str
    domain: str
    business_rule: str
    rule_id: str

    # Status / Supervisor
    valid: bool
    enrichment: dict
    mismatch_flag: bool
    entity_status: str
    entity_resolution_confidence: str
    cache_hit: bool
    cache_data: Any
    routing_tier: str
    tool_budget: list

    # Core workflow data
    reports: Annotated[dict, merge_reports]
    collected_evidence: Annotated[dict, merge_reports]
    reconciled_profile: dict
    merged: dict
    conflict_flags: list
    claims_verification: dict
    fact_check: dict
    accuracy_score: float

    # Output / Assessment
    risk_assessment: dict
    risk_category: str
    underwriting_rationale: dict
    modifier_scores: dict
    confidence_score: float
    confidence_band: str
    human_escalation_flag: bool
    audit_logs: list
    token_summary: dict

def supervisor_routing(state: CyberRiskRatingState) -> str:
    if not state.get("valid"):
        return "__end__"
    if state.get("cache_hit"):
        return "coordinator"
    return "collectors_fanout"

def build_cyber_risk_rating_graph(enable_cache: bool = True):
    rule_id = "cyber_risk_rating"
    factory = AgentFactory.for_rule(rule_id)
    cache = get_cache_manager()

    # Create collectors
    wiki_base = factory.create_collector_agent("wikipedia", WikipediaCollectorAgent)
    wikidata_base = factory.create_collector_agent("wikidata", WikidataCollectorAgent)
    sec_base = factory.create_collector_agent("sec", SECCollectorAgent)
    dnb_base = factory.create_collector_agent("dnb", DNBCollectorAgent)
    domain_base = factory.create_collector_agent("domain", DomainScraperCollectorAgent)
    responses_base = factory.create_collector_agent("responses", ResponsesAPICollectorAgent)

    # Wrap with cache if enabled
    wiki = CachingCollectorWrapper(wiki_base, "wikipedia", rule_id, cache) if enable_cache and cache.enabled else wiki_base
    wikidata = CachingCollectorWrapper(wikidata_base, "wikidata", rule_id, cache) if enable_cache and cache.enabled else wikidata_base
    sec = CachingCollectorWrapper(sec_base, "sec", rule_id, cache) if enable_cache and cache.enabled else sec_base
    dnb = CachingCollectorWrapper(dnb_base, "dnb", rule_id, cache) if enable_cache and cache.enabled else dnb_base
    domain_agent = CachingCollectorWrapper(domain_base, "domain", rule_id, cache) if enable_cache and cache.enabled else domain_base
    responses = CachingCollectorWrapper(responses_base, "responses", rule_id, cache) if enable_cache and cache.enabled else responses_base

    # Create processors
    coordinator = factory.create_coordinator(CollectionCoordinatorAgent)
    fact_checker = factory.create_fact_checker(FactCheckerAgent)
    underwriter = factory.create_underwriter(UnderwriterAgent)

    # Retries for Groq API limits
    api_retry = RetryPolicy(max_attempts=3, initial_interval=2.0, backoff_factor=2.0)

    # 1. Define Node functions
    async def wiki_node(state: CyberRiskRatingState) -> dict:
        rep = await wiki.collect(state["company_name"], state["domain"])
        # Format results for both state layouts (reports and collected_evidence)
        return {"reports": {"Wikipedia": rep}, "collected_evidence": {"Wikipedia": rep}}

    async def wikidata_node(state: CyberRiskRatingState) -> dict:
        rep = await wikidata.collect(state["company_name"], state["domain"])
        return {"reports": {"Wikidata": rep}, "collected_evidence": {"Wikidata": rep}}

    async def sec_node(state: CyberRiskRatingState) -> dict:
        rep = await sec.collect(state["company_name"], state["domain"])
        return {"reports": {"SECCollector": rep}, "collected_evidence": {"SECCollector": rep}}

    async def dnb_node(state: CyberRiskRatingState) -> dict:
        rep = await dnb.collect(state["company_name"], state["domain"])
        return {"reports": {"DBCollector": rep}, "collected_evidence": {"DBCollector": rep}}

    async def domain_node(state: CyberRiskRatingState) -> dict:
        rep = await domain_agent.collect(state["company_name"], state["domain"])
        return {"reports": {"DomainScraper": rep}, "collected_evidence": {"DomainScraper": rep}}

    async def responses_node(state: CyberRiskRatingState) -> dict:
        rep = await responses.collect(state["company_name"], state["domain"])
        return {"reports": {"ResponsesAPI": rep}, "collected_evidence": {"ResponsesAPI": rep}}

    async def coordinator_node(state: CyberRiskRatingState) -> dict:
        # If cache hit, restore reports/collected_evidence from cached data
        if state.get("cache_hit") and state.get("cache_data"):
            cache_data = state["cache_data"]
            evidence = cache_data.get("collected_evidence", {})
            return {
                "reports": evidence,
                "collected_evidence": evidence,
                **(await coordinator.coordinate({**state, "reports": evidence}))
            }
        return await coordinator.coordinate(state)

    async def fact_checker_node(state: CyberRiskRatingState) -> dict:
        res = await fact_checker.verify(state)
        return {"fact_check": res, **res}

    async def underwriter_node(state: CyberRiskRatingState) -> dict:
        # Add Business Rule to input variables
        state["business_rule"] = underwriter.config.business_rule
        res = underwriter.underwrite(state)
        return {"risk_assessment": res, **res, "token_summary": factory.tracker.get_summary()}

    # 2. Build graph structure
    g = StateGraph(CyberRiskRatingState)
    g.add_node("supervisor_node", supervisor_node)
    
    # Collectors
    g.add_node("wiki", wiki_node, retry_policy=api_retry)
    g.add_node("wikidata", wikidata_node, retry_policy=api_retry)
    g.add_node("sec", sec_node, retry_policy=api_retry)
    g.add_node("dnb", dnb_node, retry_policy=api_retry)
    g.add_node("domain", domain_node, retry_policy=api_retry)
    g.add_node("responses", responses_node, retry_policy=api_retry)

    # Processors
    g.add_node("coordinator", coordinator_node, retry_policy=api_retry)
    g.add_node("fact_checker", fact_checker_node, retry_policy=api_retry)
    g.add_node("underwriter", underwriter_node, retry_policy=api_retry)

    # Entrypoint
    g.set_entry_point("supervisor_node")

    # Routing from Supervisor
    g.add_conditional_edges(
        "supervisor_node",
        supervisor_routing,
        {
            "collectors_fanout": "wiki",
            "coordinator": "coordinator",
            "__end__": END
        }
    )
    # Fanout connections
    g.add_conditional_edges(
        "supervisor_node",
        lambda x: ["wikidata", "sec", "dnb", "domain", "responses"] if (x.get("valid") and not x.get("cache_hit")) else [],
        {
            "wikidata": "wikidata",
            "sec": "sec",
            "dnb": "dnb",
            "domain": "domain",
            "responses": "responses"
        }
    )

    # Fanin connections to Coordinator
    g.add_edge("wiki", "coordinator")
    g.add_edge("wikidata", "coordinator")
    g.add_edge("sec", "coordinator")
    g.add_edge("dnb", "coordinator")
    g.add_edge("domain", "coordinator")
    g.add_edge("responses", "coordinator")

    # Sequential processors
    g.add_edge("coordinator", "fact_checker")
    g.add_edge("fact_checker", "underwriter")
    g.add_edge("underwriter", END)

    return g.compile()
