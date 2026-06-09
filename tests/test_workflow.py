import unittest
import os
from unittest import IsolatedAsyncioTestCase
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
        # Check if Groq API Key is set in system environment
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            self.skipTest("Skipping end-to-end integration test because GROQ_API_KEY is not set.")

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
        
        # 1. First execution - Cache Miss (calls real Groq API)
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
