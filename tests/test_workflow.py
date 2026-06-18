import unittest
import os
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch
from src.workflows import build_cyber_risk_rating_graph
from src.cache import get_cache_manager

# Register rules
import src.rules as _rules

class TestWorkflowIntegration(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Clear cache before running integration tests to ensure deterministic runs
        self.cache_path = "data/cache/company_cache.json"
        if os.path.exists(self.cache_path):
            try:
                os.remove(self.cache_path)
            except Exception:
                pass
        self.app = build_cyber_risk_rating_graph(enable_cache=True)

    async def test_validation_reject(self):
        # Empty name and domain should set valid to False and stop immediately
        state = {
            "company_name": "",
            "domain": "",
            "rule_id": "cyber_risk_rating",
            "valid": False,
            "enrichment": {},
            "mismatch_flag": False,
            "entity_status": "Match",
            "entity_resolution_confidence": "High",
            "cache_hit": False,
            "cache_data": None,
            "routing_tier": "Unknown / Tiny",
            "tool_budget": [],
            "reports": {},
            "collected_evidence": {},
            "reconciled_profile": {},
            "conflict_flags": [],
            "claims_verification": {},
            "accuracy_score": 0.0,
            "risk_category": "Average",
            "underwriting_rationale": {},
            "modifier_scores": {},
            "confidence_score": 0.0,
            "confidence_band": "Low",
            "human_escalation_flag": False,
            "audit_logs": []
        }
        res = await self.app.ainvoke(state)
        self.assertFalse(res["valid"])

    async def test_workflow_execution_and_cache(self):
        state = {
            "company_name": "TechGiant Inc.",
            "domain": "techgiant.com",
            "rule_id": "cyber_risk_rating",
            "valid": False,
            "enrichment": {},
            "mismatch_flag": False,
            "entity_status": "Match",
            "entity_resolution_confidence": "High",
            "cache_hit": False,
            "cache_data": None,
            "routing_tier": "Unknown / Tiny",
            "tool_budget": [],
            "reports": {},
            "collected_evidence": {},
            "reconciled_profile": {},
            "conflict_flags": [],
            "claims_verification": {},
            "accuracy_score": 0.0,
            "risk_category": "Average",
            "underwriting_rationale": {},
            "modifier_scores": {},
            "confidence_score": 0.0,
            "confidence_band": "Low",
            "human_escalation_flag": False,
            "audit_logs": []
        }
        
        # Define mock behavior for the LLM
        def mock_call_llm(self_agent, prompt: str, temperature: float = 0.0) -> str:
            if self_agent.tracker:
                self_agent.tracker.add_usage(100, 50)
                
            agent_name = getattr(self_agent.config, 'name', self_agent.__class__.__name__).lower()
            if "coordinator" in agent_name:
                return '{"revenue": 2000000000, "subsidiaries": ["Sub1"], "acquisitions": [], "customer_type": "B2B", "has_ecommerce": false, "countries_of_operation": ["US"], "privacy_policy_published": true}'
            elif "fact checker" in agent_name or "fact_checker" in agent_name or "factchecker" in agent_name:
                return '{"claims_verification": {"revenue": {"status": "Verified", "sources_count": 1}, "subsidiaries_count": {"status": "Verified", "sources_count": 1}, "acquisitions_count": {"status": "Verified", "sources_count": 1}, "customer_type": {"status": "Verified", "sources_count": 1}, "has_ecommerce": {"status": "Verified", "sources_count": 1}, "privacy_policy_published": {"status": "Verified", "sources_count": 1}}}'
            elif "underwriter" in agent_name:
                return '{"risk_category": "Favourable", "underwriting_rationale": {"Mergers and Acquisitions": "None", "Amount of sensitive information": "B2B", "Domain Encryption": "HTTPS", "Geographic Spread": "US", "Internet footprint": "Low", "Nature of services": "Medium", "Organizational Complexity": "Low", "Privacy Regulation": "CCPA", "Seasonality of sales": "None", "Volatility/Recovery in Sales": "None", "Applicability of Privacy Regulation": "CCPA", "B2C End Products": "None", "Years in business": "20"}}'
            elif "wikipedia" in agent_name:
                return '{"country": "USA", "founding_year": 1999, "industry_classification": ["Technology"], "subsidiaries": [], "acquisitions": [], "customer_type": "B2B", "has_ecommerce": false}'
            elif "wikidata" in agent_name:
                return '{"country": "USA", "founding_year": 1999, "official_website": "https://techgiant.com", "headquarters": "New York", "industry": ["Technology"], "sub_industries": ["Software"], "subsidiaries": []}'
            elif "sec" in agent_name:
                return '{"revenue": 2000000000, "fiscal_year": 2025, "subsidiaries_count": 5, "quarterly_revenue": [500000000, 500000000, 500000000, 500000000]}'
            elif "domain" in agent_name:
                return '{"domains": [{"url": "techgiant.com", "https_encrypted": true}], "privacy_policy_published": true, "compliance_mentions": [], "customer_type": "B2B", "has_ecommerce": false}'
            return '{}'

        with patch('src.base_agents.BaseAgent.call_llm', new=mock_call_llm):
            # 1. First execution - Cache Miss (calls mock)
            res_miss = await self.app.ainvoke(state)
            self.assertTrue(res_miss["valid"])
            self.assertFalse(res_miss["cache_hit"])
            self.assertTrue(len(res_miss["modifier_scores"]) > 0)
            self.assertTrue(res_miss["confidence_score"] > 0)

            # Write to cache to simulate cli.py caching behavior for the second execution
            cache_mgr = get_cache_manager()
            profile_summary = {
                "collected_evidence": res_miss.get("collected_evidence", {}),
                "cache_type": "collector_cache"
            }
            cache_mgr.write(state["company_name"], state["domain"], profile_summary)
            
            # 2. Second execution - Cache Hit (re-runs without API calls)
            res_hit = await self.app.ainvoke(state)
            self.assertTrue(res_hit["valid"])
            self.assertTrue(res_hit["cache_hit"])
            self.assertIsNotNone(res_hit["cache_data"])
            self.assertEqual(res_hit["cache_data"]["cache_type"], "collector_cache")
            self.assertEqual(res_hit["risk_category"], res_miss["risk_category"])

if __name__ == "__main__":
    unittest.main()
