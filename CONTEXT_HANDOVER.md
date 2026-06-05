# Cyber Risk Insurance Underwriting Predictor — Context Handoff Guide

This document is designed to bring a new AI coding assistant / IDE agent completely up to speed on the **Cyber Risk Predictor** project. By reading this guide, the new agent will understand the architecture, current codebase, rules, and what tasks are queued for implementation next.

---

## 1. Project Overview & Architecture

The objective is to build a local, agentic **Cyber Risk Underwriting Predictor** in Python using **LangGraph** to automate the underwriting modifier assessment process for cyber insurance.

### System Architecture Flow (Left-to-Right)
1. **Input:** Underwriter supplies the `Company Name` and `Domain` (plus the deterministic Excel rule sheet).
2. **Supervisor Node:** Validates the input, runs wrong entity keyword check, auto-detects TLD/Country, and performs a **3-tier cache lookup** (Exact Match $\rightarrow$ Fuzzy Match $\rightarrow$ Domain Match).
   - *If cache hits:* Skips directly to Output.
   - *If cache misses:* Continues to Collectors Node (bypassing the Revenue Router for now).
3. **Revenue Router (Bypassed / Future Scope):** Checks company size/revenue and determines the **Tool Budget** (which parallel data collectors can run).
   - *Note: This node is currently commented out in the LangGraph setup to run all core collectors by default. The code is preserved so it can be enabled easily in the future.*
4. **Parallel Collectors:** 6 concurrent agent stubs query source data:
   - **WebSearch** (Bing Search API placeholder)
   - **DomainScraper** (HTTPS/SSL certificate validation placeholder)
   - **Wikipedia** (Wikipedia summary lookup placeholder)
   - **DBCollector** (Dun & Bradstreet placeholder for revenue/SIC)
   - **SECCollector** (SEC EDGAR filings placeholder)
   - **ResponsesAPI** (Standard responses database placeholder)
   - *Note: Since the router is bypassed, the system defaults to running all 6 core tools for every company.*
5. **Coordinator Node:** Reconciles findings from all parallel collectors.
   - Merges values using priority rules (e.g., for revenue: SEC > D&B > Wikipedia).
   - Flags discrepancies (Conflict flags) when sources significantly disagree.
6. **Fact Checker Node:** Performs validation of facts, checks agreement between sources, and calculates an overall **Accuracy Score** (0.0 to 1.0) and status (`[OK]`, `[I] Partial`, `[X] Contradictory`).
7. **Underwriter Node:** Evaluates the company against **10 custom underwriting modifiers** defined in the Excel sheet (`data/cyber_rater_modifier_summary.xlsx`). It generates risk ratings and applies **Deterministic Guardrails** (ensuring final scores align mathematically with Excel rules, overriding any LLM error).
   - If Accuracy Score < 50% or severe contradictions exist, it triggers a **Human Escalation Flag**.
8. **Output:** Risk Category (Very Favourable $\rightarrow$ Unfavourable), Confidence Score, full breakdown of the 10 modifiers, underwriting rationale, human escalation flag, and audit trail.

---

## 2. The 10 Underwriting Modifiers

All 10 modifiers are defined in the sheet `Sheet1` of `data/cyber_rater_modifier_summary.xlsx` and read dynamically:
1. **Mergers and Acquisitions:** Calculation: `Sum(Acquisition Points * Recency Multiplier)` mapped to revenue tiers.
2. **Amount of sensitive information:** Matrix lookup based on Customer Type (B2B vs B2C) and E-commerce Presence (True/False).
3. **Domain Encryption:** Ratio of HTTPS-encrypted domains in the portfolio (e.g., "3/3" = Favourable).
4. **Geographic Spread:** Scores based on the number of continents/countries and USA presence.
5. **Internet footprint:** Calculation: `Number of Domains * Scale Multiplier` (based on Employee Count).
6. **Nature of services:** Maps the company's sub-industry appetite (e.g., 'low_risk_cyber_saas') to a rating.
7. **Organizational Complexity:** Number of subsidiaries evaluated against the company's revenue tier.
8. **Privacy Regulation:** Presence of a published Privacy Policy and count of compliance frameworks (GDPR, CCPA, HIPAA, etc.).
9. **Seasonality of sales:** Coefficient of Variation (CV) of quarterly revenues mapped to tiers.
10. **Volatility/Recovery in Sales:** Averages three risk dimensions (Digital Exposure, Disruption Speed, Recovery Complexity) from 1 to 5.

---

## 3. Directory Structure

```
CyberRiskInsurance/
├── CONTEXT_HANDOVER.md         # This handoff file
├── requirements.txt            # Python dependencies (pandas, openpyxl, langgraph, etc.)
├── config/
│   └── config.json             # App configs (cache DB path, LLM details, temperature)
├── data/
│   ├── cyber_rater_modifier_summary.xlsx  # Excel modifiers definitions (underwriter rules)
│   ├── cache/
│   │   └── company_cache.json  # 3-tier persistence database (JSON format)
│   └── mock_sources/
│       └── mock_companies.json # Simulated research database for local API testing
├── src/
│   ├── main.py                 # CLI entrypoint to evaluate a company
│   ├── state.py                # TypedDict defining the LangGraph workflow state
│   ├── supervisor.py           # Supervisor Node (validation, cache lookup)
│   ├── router.py               # Revenue Router Node (tier routing & budget allocation)
│   ├── coordinator.py          # Coordinator Node (priority merging & entity validation)
│   ├── fact_checker.py         # Fact Checker Node (accuracy score & claims verification)
│   ├── underwriter.py          # Underwriter Node (rating evaluation & escalation checks)
│   ├── collectors/
│   │   ├── base.py             # BaseCollector with mock data loader helpers
│   │   ├── db_collector.py     # D&B API stub
│   │   ├── domain_scraper.py   # Domain HTTPS scraper stub
│   │   ├── responses_api.py    # Responses API stub
│   │   ├── sec_collector.py    # SEC EDGAR collector stub
│   │   ├── web_search.py       # Web/Bing search stub
│   │   └── wikipedia.py        # Wikipedia stub
│   └── utils/
│       ├── cache_manager.py    # 3-tier exact/fuzzy/domain cache implementation
│       └── rules_engine.py     # Dynamic Excel-driven parser & modifier calculations
└── tests/
    ├── test_modifiers.py       # Unit tests verifying all 10 modifier calculations
    └── test_workflow.py        # Integration tests verifying the LangGraph workflow
```

---

## 4. Current Implementation Details

### Cache Lookup Logic (`cache_manager.py`)
- **Exact Match:** Tries to match the exact string `{Company Name} ({Domain})`.
- **Fuzzy Match:** Computes token-based similarity between the search company name and cached company names. If similarity is above 85% (configurable), returns the cached record.
- **Domain Match:** Extracts the primary domain (e.g., `techgiant.com`) and matches it against domain keys in the cache, allowing matching even if name variants differ.

### Mock Database (`mock_companies.json`)
Contains rich mock data profiles for test companies (such as `TechGiant Inc.`, `RetailFlow Corp`, and `LocalShop LLC`). Stubs load profiles from this file using the helper `_get_mock_company_data` inside `BaseCollector` to simulate real API findings.

---

## 5. Instructions to Run and Test

### Prerequisites
Install the dependencies:
```bash
pip3 install -r requirements.txt
```

### Run Evaluation CLI
To run the end-to-end evaluation flow for a company:
```bash
PYTHONPATH=. python3 src/main.py --name "TechGiant Inc." --domain "techgiant.com"
```

### Run Tests
To run all unit tests verifying the 10 modifiers and LangGraph state workflow:
```bash
python3 -m unittest discover -s tests
```

---

## 6. Next Steps for Development

1. **LLM Integration Layer:**
   - Integrate **Gemini 2.5 Flash** (via `langchain-google-genai` or Vertex AI) into `coordinator.py`, `fact_checker.py`, and `underwriter.py` to replace static logic with agentic reasoning.
   - Use LLM prompts to synthesize written rationale descriptions, detect nuances, flag semantic contradictions, and format outputs.
   - Maintain the **Deterministic Guardrails** inside `rules_engine.py` as a strict verification layer on top of LLM outputs to override any numerical hallucinations.
2. **Real API Integrations:**
   - Swap the collector stubs in `src/collectors/` with real API endpoints (e.g., D&B Direct+, Bing Search API, SEC EDGAR RSS, etc.).
3. **Application Layer:**
   - Wrap the LangGraph workflow in a web server (e.g. **FastAPI**).
   - Design a frontend (e.g. **React** or **Streamlit**) for underwriters to review evaluations, configure Excel sheets, and handle cases flagged for Human Escalation.
