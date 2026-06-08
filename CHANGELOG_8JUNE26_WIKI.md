# CyberRiskInsurance — Code Changes & Bug Fixes (June 8, 2026)

---

## 1. Migration from Mock Data to Real Open-Source APIs

**What:** Replaced all hardcoded mock company data with live API calls to publicly available, free open-source data sources.

**Why:** The project previously used a static `mock_companies.json` file for demo testing. This made the system non-functional for unknown companies and introduced test bias. Real APIs allow the system to evaluate any company dynamically.

**Where (Files Changed):**
- `src/collectors/db_collector.py` → Now queries **GLEIF Fuzzy Completions API** (legal entity lookup by name)
- `src/collectors/domain_scraper.py` → Now performs a real **SSL socket probe** on port 443 to verify HTTPS status
- `src/collectors/sec_collector.py` → Now queries **SEC EDGAR API** (CIK resolution, XBRL company facts, Exhibit 21 subsidiary parsing)
- `src/collectors/wikipedia.py` → Now queries **Wikipedia Search API** (intro extract, country inference, subsidiary mention detection)
- `src/collectors/web_search.py` → Gracefully skips if `BING_API_KEY` is not present (no crash)
- `src/collectors/responses_api.py` → Gracefully skips if `ENABLE_RESPONSES_API` env var is not set

**Impact:** System can now evaluate real companies using publicly available data. No dependency on mock files. External API failures return a `status: error` or `status: skipped` result without crashing the graph.

---

## 2. New Wikidata Collector

**What:** Added a brand new collector, `WikidataCollector`, that queries the **Wikidata Action API** to extract company facts.

**Why:** Wikidata provides freely accessible structured data including company country, headquarters, parent company, subsidiaries, revenue, and official website — none of which were available without this collector.

**Where (Files Changed):**
- `src/collectors/wikidata.py` → Created (new file)
- `src/collectors/__init__.py` → Exported `WikidataCollector`
- `src/graph.py` → Added to `collectors_map` and included in the default tool budget

**Impact:** Provides the coordinator with a high-quality, freely available third source for revenue, country, subsidiaries, and official website validation — increasing reconciliation accuracy.

---

## 3. Collector-Side Cache Strategy

**What:** Changed what is stored in the cache. Previously the final underwriting verdict (risk category, scores) was cached. Now only the raw collected evidence (web-scraped data) is cached.

**Why:** The old strategy meant that if modifier rules were updated or bugs were fixed in the rules engine, cached companies would still return stale scores. The only fix was to manually delete the cache and re-scrape the internet — expensive and slow.

**Where (Files Changed):**
- `src/underwriter.py` → Cache write now stores `{ "collected_evidence": {...}, "cache_type": "collector_cache" }` instead of final scores
- `src/supervisor.py` → On cache hit, restores `collected_evidence` from cache into state
- `src/graph.py` → Cache hits now route to `coordinator_node` (not `END`) so scoring is always freshly re-evaluated

**Impact:** Rules engine changes now take effect immediately for all cached companies without re-scraping. The expensive internet scraping is cached; the cheap rules evaluation always runs fresh.

---

## 4. Coordinator & Fact Checker — Multi-Source Reconciliation

**What:** Rewrote reconciliation and fact-checking logic to support all new real API sources using a defined trust priority ranking.

**Why:** With multiple real data sources now providing different values (e.g., SEC revenue vs Wikidata revenue), the system needed clear rules on which source to trust and how to detect real contradictions vs. minor variances.

**Where (Files Changed):**
- `src/coordinator.py` → Trust ranking: `SEC > GLEIF > DomainScraper > Wikidata > Wikipedia > WebSearch`. Added contradiction checks (zero vs. >$1M revenue, >5x revenue difference, domain vs. Wikidata official website mismatch). Geographic deduplication across all sources.
- `src/fact_checker.py` → Updated to count evidence from all new collectors. Added fix: empty dictionaries `{}` (e.g. GLEIF returning no parent relationships) are no longer counted as valid evidence.
- `src/utils/rules_engine.py` → Revenue defaults safely to `0` if `None`, preventing `TypeError` crashes when SEC has no revenue data.

**Impact:** More accurate reconciliation across 7 sources. Fewer false contradictions. Cleaner confidence scoring.

---

## 5. Bug Fix — Graph Compilation Crash [Bug 1]

**What:** Fixed a crash that would occur at startup when the coworker's changes referenced `router_node` in the conditional routing but that node was commented out.

**Why:** The Revenue Router is future scope and intentionally commented out. The coworker's routing update incorrectly tried to return `"router_node"` on cache miss, causing `ValueError: Node 'router_node' is not registered`.

**Where:** `src/graph.py` — `supervisor_routing` returns `"collectors_node"` on cache miss. Router node and its edges remain fully commented out.

**Impact:** Graph compiles and runs without error. Revenue Router remains available for future activation.

---

## 6. Bug Fix — Integration Test Cache Assertion Failure [Bug 2]

**What:** Fixed a `KeyError` that would crash the test suite on cache-hit runs.

**Why:** After the new cache strategy stored raw evidence instead of final scores, the integration test still tried to read `cache_data["risk_category"]` — a key that no longer exists in the cache.

**Where:** `tests/test_workflow.py` — Assertion updated to check `cache_data["cache_type"] == "collector_cache"` and `res_hit["risk_category"] == "Favourable"` (from the freshly computed state, not from cache).

**Impact:** All 6 integration and modifier tests pass cleanly.

---

## 7. Bug Fix — Misleading Entity Resolution Confidence [Bug 3]

**What:** Fixed a logic gap where a domain mismatch was flagged (`entity_status = "Mismatch"`) but confidence was left at the default `"High"`, creating a contradictory output.

**Why:** During a refactor to add domain aliases (e.g., TCS → tcs.com), the line `entity_resolution_confidence = "Low"` was accidentally removed from the mismatch block. The system would then report high confidence in a company it just flagged as the wrong entity.

**Where:** `src/supervisor.py` — All mismatch paths now explicitly set `entity_resolution_confidence = "Low"`.

**Impact:** Underwriter now correctly zeroes out the confidence score when entity status is `"Mismatch"`, and human escalation triggers as expected.

---

## 8. Additional Fix — Mismatch Detection Logic Reordering

**What:** Reordered entity mismatch detection so that keyword-based checks fire before slug-based checks.

**Why:** The slug check (`"amazon" in "amazon-river.org"`) was incorrectly marking mismatched domains as a match because the company name string appeared inside an unrelated domain. This caused `test_entity_mismatch` to fail.

**Where:** `src/supervisor.py` — Detection order is now: (1) `WRONG_ENTITY_KEYWORDS` → (2) Domain aliases → (3) Slug/word match → (4) Generic mismatch fallback.

**Impact:** Entity mismatch correctly detected for known adversarial inputs (e.g., Amazon → amazon-river.org). All mismatch tests pass.

---

## Files Changed Summary

| File | Type of Change |
|---|---|
| `src/collectors/wikidata.py` | **New** |
| `src/collectors/db_collector.py` | Real API (GLEIF) |
| `src/collectors/domain_scraper.py` | Real API (SSL probe) |
| `src/collectors/sec_collector.py` | Real API (SEC EDGAR) |
| `src/collectors/wikipedia.py` | Real API (Wikipedia Search) |
| `src/collectors/web_search.py` | Guarded stub |
| `src/collectors/responses_api.py` | Guarded stub |
| `src/collectors/__init__.py` | Export WikidataCollector |
| `src/coordinator.py` | Multi-source reconciliation |
| `src/fact_checker.py` | Multi-source claims + dict fix |
| `src/supervisor.py` | Entity resolution, cache restore, Bug 3 & 8 fix |
| `src/underwriter.py` | Collector-side cache write, escalation fix |
| `src/graph.py` | Bug 1 fix, Wikidata budget, cache hit routing |
| `src/state.py` | Added `entity_status`, `entity_resolution_confidence` |
| `src/main.py` | Updated CLI output for new state fields |
| `src/utils/rules_engine.py` | None-safe revenue handling |
| `src/router.py` | Internal budget logic (node remains commented out) |
| `tests/test_workflow.py` | Bug 2 fix, new state fields in test dicts |
| `.gitignore` | Added `.env` |

**Test Result: 6/6 PASSED ✅**

