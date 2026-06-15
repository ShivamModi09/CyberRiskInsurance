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

    def test_sec_collector_revenue_extraction(self):
        # Test that SECCollectorAgent correctly chooses the best revenue key
        # and extracts the latest annual and chronological deduplicated quarterly revenues.
        from src.collectors import SECCollectorAgent
        from unittest.mock import patch, MagicMock
        import json
        
        collector = self.factory.create_collector_agent("sec", SECCollectorAgent)
        
        # Mock company tickers JSON response
        mock_tickers = {
            "0": {"cik_str": 1297989, "ticker": "EXLS", "title": "ExlService Holdings, Inc."}
        }
        
        # Mock CIK JSON response with multiple keys (SalesRevenueNet ending 2013 and RevenueFromContractWithCustomerExcludingAssessedTax ending 2025)
        mock_facts = {
            "facts": {
                "us-gaap": {
                    "SalesRevenueNet": {
                        "units": {
                            "USD": [
                                # Old 10-K entry for 2013
                                {"start": "2013-01-01", "end": "2013-12-31", "val": 124000000, "form": "10-K", "fy": 2013, "fp": "FY", "filed": "2014-03-03"}
                            ]
                        }
                    },
                    "RevenueFromContractWithCustomerExcludingAssessedTax": {
                        "units": {
                            "USD": [
                                # 2024 10-K annual entry
                                {"start": "2024-01-01", "end": "2024-12-31", "val": 1800000000, "form": "10-K", "fy": 2024, "fp": "FY", "filed": "2025-02-25"},
                                # 2025 10-K annual entry
                                {"start": "2025-01-01", "end": "2025-12-31", "val": 2000000000, "form": "10-K", "fy": 2025, "fp": "FY", "filed": "2026-02-24"},
                                # 2025 Q1 10-Q entry (3-month duration)
                                {"start": "2025-01-01", "end": "2025-03-31", "val": 450000000, "form": "10-Q", "fy": 2025, "fp": "Q1", "filed": "2025-05-01"},
                                # 2025 Q2 10-Q entry (3-month duration)
                                {"start": "2025-04-01", "end": "2025-06-30", "val": 480000000, "form": "10-Q", "fy": 2025, "fp": "Q2", "filed": "2025-08-01"},
                                # 2025 Q2 YTD 10-Q entry (6-month duration, should be ignored for quarterly list)
                                {"start": "2025-01-01", "end": "2025-06-30", "val": 930000000, "form": "10-Q", "fy": 2025, "fp": "Q2", "filed": "2025-08-01"}
                            ]
                        }
                    }
                }
            }
        }
        
        # Mock urlopen calls
        def mock_urlopen(req, *args, **kwargs):
            url = req.full_url if hasattr(req, 'full_url') else req
            mock_res = MagicMock()
            mock_res.__enter__.return_value = mock_res
            if "company_tickers.json" in url:
                mock_res.read.return_value = json.dumps(mock_tickers).encode()
            elif "CIK0001297989.json" in url:
                mock_res.read.return_value = json.dumps(mock_facts).encode()
            else:
                mock_res.read.return_value = b"{}"
            return mock_res
            
        with patch('urllib.request.urlopen', side_effect=mock_urlopen):
            # Mock call_llm because we don't want to hit Groq API in this unit test
            collector.call_llm = lambda prompt, temp=0.0: '{"revenue": 2000000000, "fiscal_year": 2025, "subsidiaries_count": 0, "quarterly_revenue": []}'
            import asyncio
            res = asyncio.run(collector.collect("ExlService Holdings, Inc.", "exlservice.com"))
            
            self.assertEqual(res["status"], "success")
            findings = res["findings"]
            
            # Annual revenue should be the latest (2,000,000,000) from the newer key
            self.assertEqual(findings["revenue"], 2000000000)
            self.assertEqual(findings["fiscal_year"], 2025)
            
            # Quarterly revenue list should contain the two 3-month period values (450M and 480M) but ignore the 6-month YTD one (930M)
            self.assertEqual(findings["quarterly_revenue"], [450000000, 480000000])

if __name__ == "__main__":
    unittest.main()
