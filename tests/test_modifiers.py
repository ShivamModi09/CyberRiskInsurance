import unittest
import os
from src.config import BusinessRuleConfig
from src.registry import BusinessRuleRegistry
from src.factory import AgentFactory
from src.processors import UnderwriterAgent

# Trigger registration on import
import src.rules as _rules

class TestModifiersAndParser(unittest.TestCase):
    def setUp(self):
        self.factory = AgentFactory.for_rule("cyber_risk_rating")
        self.underwriter = self.factory.create_underwriter(UnderwriterAgent)

    def test_rule_registration(self):
        rules = BusinessRuleRegistry.list_rules()
        self.assertIn("cyber_risk_rating", rules)
        
        cfg = BusinessRuleRegistry.get("cyber_risk_rating")
        self.assertIsNotNone(cfg)
        self.assertEqual(cfg.rule_id, "cyber_risk_rating")

    def test_underwriter_org_complexity(self):
        # 1. Test Org Complexity for >$1B company with 11 subsidiaries (favourable)
        state_large = {
            "company_name": "Test Large",
            "domain": "test.com",
            "accuracy_score": 1.0,
            "mismatch_flag": False,
            "conflict_flags": [],
            "reconciled_profile": {
                "revenue": 1200000000,
                "subsidiaries": ["Sub1", "Sub2", "Sub3", "Sub4", "Sub5", "Sub6", "Sub7", "Sub8", "Sub9", "Sub10", "Sub11"],
                "acquisitions": [],
                "customer_type": "B2B",
                "has_ecommerce": False,
                "domains": [{"url": "test.com", "https_encrypted": True}],
                "countries_of_operation": ["USA"],
                "continent_spread": ["North America"]
            }
        }
        # Mock LLM call to return standard formatting
        self.underwriter.call_llm = lambda prompt, temp=0.0: '{"risk_category": "Favourable", "underwriting_rationale": {"Organizational Complexity": "Reconciled ok"}}'
        res = self.underwriter.underwrite(state_large)
        self.assertEqual(res["modifier_scores"]["Organizational Complexity"]["rating"], "favourable")

        # 2. Test Org Complexity for <$50M company with 12 subsidiaries (partially unfavourable)
        state_small = {
            "company_name": "Test Small",
            "domain": "test.com",
            "accuracy_score": 1.0,
            "mismatch_flag": False,
            "conflict_flags": [],
            "reconciled_profile": {
                "revenue": 10000000,
                "subsidiaries": ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10", "S11", "S12"],
                "acquisitions": [],
                "customer_type": "B2B",
                "has_ecommerce": False,
                "domains": [{"url": "test.com", "https_encrypted": True}],
                "countries_of_operation": ["USA"],
                "continent_spread": ["North America"]
            }
        }
        res_small = self.underwriter.underwrite(state_small)
        self.assertEqual(res_small["modifier_scores"]["Organizational Complexity"]["rating"], "partially unfavourable")

    def test_underwriter_sensitive_info(self):
        # B2B, no ecommerce = favourable
        state1 = {
            "company_name": "Test B2B",
            "domain": "test.com",
            "accuracy_score": 1.0,
            "mismatch_flag": False,
            "conflict_flags": [],
            "reconciled_profile": {
                "customer_type": "B2B",
                "has_ecommerce": False
            }
        }
        self.underwriter.call_llm = lambda prompt, temp=0.0: '{"risk_category": "Favourable", "underwriting_rationale": {}}'
        res1 = self.underwriter.underwrite(state1)
        self.assertEqual(res1["modifier_scores"]["Amount of sensitive information"]["rating"], "favourable")

        # B2C, has ecommerce = Partially Unfavourable
        state2 = {
            "company_name": "Test B2C",
            "domain": "test.com",
            "accuracy_score": 1.0,
            "mismatch_flag": False,
            "conflict_flags": [],
            "reconciled_profile": {
                "customer_type": "B2C",
                "has_ecommerce": True
            }
        }
        res2 = self.underwriter.underwrite(state2)
        self.assertEqual(res2["modifier_scores"]["Amount of sensitive information"]["rating"], "partially unfavourable")

    def test_underwriter_years_in_business(self):
        # 1. >$1B revenue, yib = 35 (very favourable)
        state_large = {
            "company_name": "Large Old Co",
            "domain": "largeold.com",
            "accuracy_score": 1.0,
            "mismatch_flag": False,
            "conflict_flags": [],
            "reconciled_profile": {
                "revenue": 1500000000,
                "founding_year": 1990
            }
        }
        self.underwriter.call_llm = lambda prompt, temp=0.0: '{"risk_category": "Favourable", "underwriting_rationale": {}}'
        res = self.underwriter.underwrite(state_large)
        self.assertEqual(res["modifier_scores"]["Years in business"]["rating"], "very favourable")

        # 2. <$50M revenue, yib = 2 (average)
        state_small = {
            "company_name": "Small Startup",
            "domain": "startup.com",
            "accuracy_score": 1.0,
            "mismatch_flag": False,
            "conflict_flags": [],
            "reconciled_profile": {
                "revenue": 5000000,
                "founding_year": 2024
            }
        }
        res2 = self.underwriter.underwrite(state_small)
        self.assertEqual(res2["modifier_scores"]["Years in business"]["rating"], "average")

if __name__ == "__main__":
    unittest.main()
