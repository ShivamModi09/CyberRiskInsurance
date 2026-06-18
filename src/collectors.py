import os
import json
import socket
import ssl
import urllib.request
import urllib.parse
from typing import Dict, Any
from src.base_agents import BaseCollectorAgent

class WikipediaCollectorAgent(BaseCollectorAgent):
    USER_AGENT = 'CyberRiskInsurancePOC/1.0 (https://github.com/ShivamModi09/CyberRiskInsurance)'

    async def collect(self, company_name: str, domain: str) -> Dict[str, Any]:
        query = urllib.parse.quote(company_name)
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&utf8=&format=json"
        
        logger = self.get_logger()
        logger.info(f"[Wikipedia Collector] Fetching search results for '{company_name}' using query '{query}'")
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&utf8=&format=json"
        
        try:
            req = urllib.request.Request(search_url, headers={'User-Agent': self.USER_AGENT})
            logger.info(f"[Wikipedia Collector] Requesting URL: {search_url} with User-Agent: {self.USER_AGENT}")
            with urllib.request.urlopen(req, timeout=5) as response:
                resp_bytes = response.read()
                logger.info(f"[Wikipedia Collector] Received search API response (status {response.status}, {len(resp_bytes)} bytes)")
                data = json.loads(resp_bytes.decode())
                
            search_results = data.get("query", {}).get("search", [])
            if not search_results:
                logger.info(f"[Wikipedia Collector] No search results returned for query '{query}'")
                return {
                    "source": self.config.source_name,
                    "status": "skipped",
                    "message": "No Wikipedia article found.",
                    "findings": {}
                }
                
            title = urllib.parse.quote(search_results[0]["title"])
            summary_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=&titles={title}&format=json"
            
            logger.info(f"[Wikipedia Collector] Requesting full extract from Wikipedia page for title '{search_results[0]['title']}'")
            logger.info(f"[Wikipedia Collector] Requesting URL: {summary_url}")
            req2 = urllib.request.Request(summary_url, headers={'User-Agent': self.USER_AGENT})
            with urllib.request.urlopen(req2, timeout=10) as response2:
                resp2_bytes = response2.read()
                logger.info(f"[Wikipedia Collector] Received extract API response (status {response2.status}, {len(resp2_bytes)} bytes)")
                summary_data = json.loads(resp2_bytes.decode())
            
            pages = summary_data.get("query", {}).get("pages", {})
            page = list(pages.values())[0] if pages else {}
            extract = page.get("extract", "")[:12000]
            logger.info(f"[Wikipedia Collector] Page extract successfully retrieved. Extract preview (first 500 chars):\n{extract[:500]}...")
            
            if not extract:
                logger.info("[Wikipedia Collector] Wikipedia extract page is empty")
                return {
                    "source": self.config.source_name,
                    "status": "skipped",
                    "message": "Wikipedia page extract is empty.",
                    "findings": {}
                }

            # Call LLM to extract fields from the Wikipedia page text
            prompt_vars = {
                "company_name": company_name,
                "domain": domain,
                "wikipedia_text": extract
            }
            prompt = self.format_prompt(self.config.prompt_template, **prompt_vars)
            response_text = self.call_llm(prompt)
            extracted = self.parse_json(response_text)
            
            # Map target fields
            findings = {k: extracted.get(k) for k in self.config.target_fields}
            logger.info(f"[Wikipedia Collector] Mapped target fields: {findings}")
            return {
                "source": self.config.source_name,
                "status": "success",
                "findings": findings
            }
        except Exception as e:
            import traceback
            logger.error(f"[Wikipedia Collector] Collection failed: {e}\nTraceback:\n{traceback.format_exc()}")
            return {
                "source": self.config.source_name,
                "status": "error",
                "message": f"{e}\nTraceback:\n{traceback.format_exc()}",
                "findings": {}
            }

class WikidataCollectorAgent(BaseCollectorAgent):
    USER_AGENT = 'CyberRiskInsurancePOC/1.0 (https://github.com/ShivamModi09/CyberRiskInsurance)'

    async def collect(self, company_name: str, domain: str) -> Dict[str, Any]:
        logger = self.get_logger()
        try:
            # 1. Search entities
            query = urllib.parse.urlencode({
                'action': 'wbsearchentities',
                'search': company_name,
                'language': 'en',
                'format': 'json',
                'limit': 5
            })
            url = f'https://www.wikidata.org/w/api.php?{query}'
            req = urllib.request.Request(url, headers={'User-Agent': self.USER_AGENT})
            
            logger.info(f"[Wikidata Collector] Resolving entity for search: '{company_name}'")
            logger.info(f"[Wikidata Collector] Requesting URL: {url}")
            with urllib.request.urlopen(req, timeout=10) as response:
                resp_bytes = response.read()
                logger.info(f"[Wikidata Collector] Received wbsearchentities response (status {response.status}, {len(resp_bytes)} bytes)")
                data = json.loads(resp_bytes.decode())
                
            search_results = data.get('search', [])
            if not search_results:
                logger.info(f"[Wikidata Collector] No entity search results resolved on Wikidata for '{company_name}'")
                return {
                    "source": self.config.source_name,
                    "status": "skipped",
                    "message": "No entity resolved on Wikidata.",
                    "findings": {}
                }
                
            qids = [res['id'] for res in search_results]
            logger.info(f"[Wikidata Collector] Search matched entity IDs: {qids}")
            
            # 2. Get entity claims
            query2 = urllib.parse.urlencode({
                'action': 'wbgetentities',
                'ids': '|'.join(qids),
                'format': 'json',
                'props': 'claims|labels'
            })
            url2 = f'https://www.wikidata.org/w/api.php?{query2}'
            req2 = urllib.request.Request(url2, headers={'User-Agent': self.USER_AGENT})
            
            logger.info(f"[Wikidata Collector] Requesting entity details for IDs: {qids}")
            logger.info(f"[Wikidata Collector] Requesting URL: {url2}")
            with urllib.request.urlopen(req2, timeout=10) as response:
                resp2_bytes = response.read()
                logger.info(f"[Wikidata Collector] Received wbgetentities response (status {response.status}, {len(resp2_bytes)} bytes)")
                data2 = json.loads(resp2_bytes.decode())
                
            entities = data2.get('entities', {})
            best_qid = None
            best_claims = {}
            
            import difflib
            for qid_candidate in qids:
                entity = entities.get(qid_candidate, {})
                label = entity.get('labels', {}).get('en', {}).get('value', '').lower()
                candidate_claims = entity.get('claims', {})
                
                websites = []
                for statement in candidate_claims.get('P856', []):
                    snak = statement.get('mainsnak', {})
                    if snak.get('snaktype') == 'value' and snak.get('datavalue', {}).get('type') == 'string':
                        websites.append(snak.get('datavalue', {}).get('value'))
                        
                domain_match = False
                for w in websites:
                    if domain.lower() in w.lower():
                        domain_match = True
                        break
                        
                sim = difflib.SequenceMatcher(None, company_name.lower(), label).ratio()
                logger.info(f"[Wikidata Collector] Evaluating entity {qid_candidate} ({label}): domain_match={domain_match}, name_similarity={sim:.2f}")
                if domain_match or sim > 0.8:
                    best_qid = qid_candidate
                    best_claims = candidate_claims
                    logger.info(f"[Wikidata Collector] Selected best entity match: {best_qid} ('{label}')")
                    break
                    
            if not best_qid:
                logger.info(f"[Wikidata Collector] Could not resolve matching company entity on Wikidata with high confidence (sim > 0.8 or domain match) out of: {qids}")
                return {
                    "source": self.config.source_name,
                    "status": "skipped",
                    "message": "Could not resolve matching company entity on Wikidata.",
                    "findings": {}
                }

            # Helper to extract basic string / amount data for LLM context
            def get_snak_value(snak):
                if snak.get('snaktype') == 'value':
                    datavalue = snak.get('datavalue', {})
                    if datavalue.get('type') == 'wikibase-entityid':
                        return datavalue.get('value', {}).get('id')
                    elif datavalue.get('type') == 'string':
                        return datavalue.get('value')
                    elif datavalue.get('type') == 'monolingualtext':
                        return datavalue.get('value', {}).get('text')
                return None

            def extract_claim_values(prop_id):
                vals = []
                for statement in best_claims.get(prop_id, []):
                    val = get_snak_value(statement.get('mainsnak', {}))
                    if val:
                        vals.append(val)
                return vals

            # Get some raw values for claims to present to LLM
            countries = extract_claim_values('P17')         # country
            hqs = extract_claim_values('P159')              # headquarters location
            industries = extract_claim_values('P452')       # industry
            websites = extract_claim_values('P856')         # official website(s)
            subsidiaries = extract_claim_values('P355')     # subsidiaries
            inception = extract_claim_values('P571')        # inception date
            owned_by = extract_claim_values('P127')         # owned by (parent/acquirer context)
            operating_areas = extract_claim_values('P159')  # areas served via HQ locations
            instance_of = extract_claim_values('P31')
            parent_org = extract_claim_values('P749')

            raw_data = {
                "qid": best_qid,
                "countries_ids": countries,
                "headquarters_ids": hqs,
                "industry_ids": industries,
                "websites": websites,
                "subsidiaries_ids": subsidiaries,
                "inception": inception,
                "owned_by_ids": owned_by,
                "parent_org_ids": parent_org,
                "instance_of_ids": instance_of,
                "operating_area_ids": operating_areas
            }
            
            logger.info(f"[Wikidata Collector] Fetched raw claims from Wikidata entity '{best_qid}': {json.dumps(raw_data)}")
            
            # Send raw details to LLM to parse and extract requested target fields
            prompt_vars = {
                "company_name": company_name,
                "domain": domain,
                "wikidata_text": json.dumps(raw_data)
            }
            prompt = self.format_prompt(self.config.prompt_template, **prompt_vars)
            response_text = self.call_llm(prompt)
            extracted = self.parse_json(response_text)
            
            findings = {k: extracted.get(k) for k in self.config.target_fields}
            logger.info(f"[Wikidata Collector] Mapped target fields: {findings}")
            return {
                "source": self.config.source_name,
                "status": "success",
                "findings": findings
            }
        except Exception as e:
            import traceback
            logger.error(f"[Wikidata Collector] Collection failed: {e}\nTraceback:\n{traceback.format_exc()}")
            return {
                "source": self.config.source_name,
                "status": "error",
                "message": f"{e}\nTraceback:\n{traceback.format_exc()}",
                "findings": {}
            }

class SECCollectorAgent(BaseCollectorAgent):
    USER_AGENT = 'CyberRiskAgent/1.0 (contact@example.com)'

    def _resolve_cik(self, company_name: str) -> tuple:
        """
        Resolve company name to (cik_str, matched_entity_name) using a 3-tier strategy:
        1. EDGAR full-text search API (efts.sec.gov) — works for private/mutual companies
        2. EDGAR company browse API (HTML-based, broader coverage)
        3. Fallback: company_tickers.json (public/ticker companies only)
        Returns (cik_padded, entity_name) or (None, None) if not found.
        """
        logger = self.get_logger()
        import re
        import difflib

        encoded = urllib.parse.quote(f'"{company_name}"')

        # --- Tier 1: EDGAR EFTS full-text search (handles private companies) ---
        try:
            search_url = f"https://efts.sec.gov/LATEST/search-index?q={encoded}&forms=10-K&hits.hits.total.value=true"
            logger.info(f"[SEC CIK Resolve] Tier 1 EFTS search URL: {search_url}")
            req = urllib.request.Request(search_url, headers={'User-Agent': self.USER_AGENT})
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_bytes = resp.read()
                logger.info(f"[SEC CIK Resolve] Tier 1 response received ({len(resp_bytes)} bytes)")
                data = json.loads(resp_bytes.decode())

            hits = data.get('hits', {}).get('hits', [])
            logger.info(f"[SEC CIK Resolve] Tier 1 hits resolved count: {len(hits)}")
            if hits:
                best_cik = None
                best_name = None
                best_score = 0.0
                for hit in hits[:10]:
                    src = hit.get('_source', {})
                    entity_name = src.get('entity_name', '')
                    acc_id = hit.get('_id', '')
                    raw_cik = acc_id.split('-')[0] if '-' in acc_id else acc_id[:10]
                    if not raw_cik.isdigit():
                        continue
                    score = difflib.SequenceMatcher(None, company_name.lower(), entity_name.lower()).ratio()
                    logger.info(f"[SEC CIK Resolve] Tier 1 matching entity '{entity_name}' CIK={raw_cik} Score={score:.2f}")
                    if score > best_score:
                        best_score = score
                        best_cik = raw_cik.zfill(10)
                        best_name = entity_name
                if best_cik and best_score > 0.4:
                    logger.info(f"[SEC CIK Resolve] Tier 1 Match Found: CIK={best_cik} Name='{best_name}' (Score={best_score:.2f})")
                    return best_cik, best_name
        except Exception as e:
            import traceback
            logger.warning(f"[SEC CIK Resolve] Tier 1 EFTS failed: {e}\n{traceback.format_exc()}")

        # --- Tier 2: EDGAR company browse API (wider net, parses XML atom feed) ---
        try:
            browse_name = urllib.parse.quote(company_name)
            browse_url = f"https://www.sec.gov/cgi-bin/browse-edgar?company={browse_name}&CIK=&type=10-K&dateb=&owner=include&count=10&search_text=&action=getcompany&output=atom"
            logger.info(f"[SEC CIK Resolve] Tier 2 browse URL: {browse_url}")
            req2 = urllib.request.Request(browse_url, headers={'User-Agent': self.USER_AGENT})
            with urllib.request.urlopen(req2, timeout=10) as resp2:
                xml_text = resp2.read().decode()
                logger.info(f"[SEC CIK Resolve] Tier 2 response size: {len(xml_text)} chars")

            cik_matches = re.findall(r'<CIK>(\d+)</CIK>', xml_text)
            name_matches = re.findall(r'<conformed-name>(.*?)</conformed-name>', xml_text, re.IGNORECASE)
            logger.info(f"[SEC CIK Resolve] Tier 2 resolved CIK matches: {cik_matches}, Name matches: {name_matches}")
            if cik_matches and name_matches:
                best_cik = None
                best_name = None
                best_score = 0.0
                for cik_val, nm in zip(cik_matches, name_matches):
                    score = difflib.SequenceMatcher(None, company_name.lower(), nm.lower()).ratio()
                    logger.info(f"[SEC CIK Resolve] Tier 2 matching candidate '{nm}' CIK={cik_val} Score={score:.2f}")
                    if score > best_score:
                        best_score = score
                        best_cik = str(cik_val).zfill(10)
                        best_name = nm
                if best_cik and best_score > 0.3:
                    logger.info(f"[SEC CIK Resolve] Tier 2 Match Found: CIK={best_cik} Name='{best_name}' (Score={best_score:.2f})")
                    return best_cik, best_name
        except Exception as e:
            import traceback
            logger.warning(f"[SEC CIK Resolve] Tier 2 browse failed: {e}\n{traceback.format_exc()}")

        # --- Tier 3: Fallback — company_tickers.json (public/ticker companies) ---
        try:
            tickers_url = "https://www.sec.gov/files/company_tickers.json"
            logger.info(f"[SEC CIK Resolve] Tier 3 query: {tickers_url}")
            req3 = urllib.request.Request(tickers_url, headers={'User-Agent': self.USER_AGENT})
            with urllib.request.urlopen(req3, timeout=10) as resp3:
                tickers_text = resp3.read().decode()
                tickers = json.loads(tickers_text)
            for _, data in tickers.items():
                if company_name.lower() in data['title'].lower():
                    logger.info(f"[SEC CIK Resolve] Tier 3 Match Found (ticker json): CIK={data['cik_str']} Name='{data['title']}'")
                    return str(data['cik_str']).zfill(10), data['title']
        except Exception as e:
            import traceback
            logger.warning(f"[SEC CIK Resolve] Tier 3 ticker lookup failed: {e}\n{traceback.format_exc()}")

        logger.info(f"[SEC CIK Resolve] CIK lookup failed across all tiers for '{company_name}'")
        return None, None

    async def collect(self, company_name: str, domain: str) -> Dict[str, Any]:
        logger = self.get_logger()
        try:
            logger.info(f"[SEC EDGAR Collector] Starting data collection for '{company_name}' ({domain})")
            # 1. Resolve Company Name to CIK via multi-tier EDGAR name search
            cik, matched_name = self._resolve_cik(company_name)

            if not cik:
                logger.info(f"[SEC EDGAR Collector] Skipped: CIK could not be resolved for '{company_name}'")
                return {
                    "source": self.config.source_name,
                    "status": "skipped",
                    "message": f"Company '{company_name}' not found in SEC EDGAR (tried EFTS search, browse API, and tickers list).",
                    "findings": {}
                }

            # 2. Fetch Company Facts
            facts_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
            logger.info(f"[SEC EDGAR Collector] Requesting Company Facts URL: {facts_url}")
            req2 = urllib.request.Request(facts_url, headers={'User-Agent': self.USER_AGENT})
            with urllib.request.urlopen(req2, timeout=10) as response:
                resp_bytes = response.read()
                logger.info(f"[SEC EDGAR Collector] Facts API response size: {len(resp_bytes)} bytes")
                facts = json.loads(resp_bytes.decode())
                
            gaap = facts.get('facts', {}).get('us-gaap', {})
            logger.info(f"[SEC EDGAR Collector] Available us-gaap metrics count: {len(gaap)}")
            
            # Find the best revenue key (the one with the latest ending 10-K/annual filing)
            best_key = None
            best_latest_end = ""
            best_usd = []
            
            from datetime import datetime

            for rk in [
                # Standard commercial/tech
                'RevenueFromContractWithCustomerExcludingAssessedTax',
                'Revenues',
                'SalesRevenueNet',
                # Insurance-specific (Liberty Mutual, Travelers, etc.)
                'PremiumsEarned',
                'PremiumsWrittenNet',
                'NetPremiumsEarned',
                'InsurancePremiumsAndOtherRevenues',
                'PolicyholderBenefitsAndClaimsIncurredNet',
                # Financial services
                'InterestAndDividendIncomeOperating',
                'RevenuesExcludingInterestAndDividends',
                'NetIncomeLoss',
            ]:
                if rk in gaap:
                    units = gaap[rk].get('units', {})
                    usd = units.get('USD', [])
                    # Find if there are any valid annual entries and what their latest end date is
                    key_latest_end = ""
                    for u in usd:
                        if 'start' in u and 'end' in u and 'val' in u:
                            try:
                                start = datetime.strptime(u['start'], "%Y-%m-%d")
                                end = datetime.strptime(u['end'], "%Y-%m-%d")
                                days = (end - start).days
                                if 330 <= days <= 390:
                                    if u['end'] > key_latest_end:
                                        key_latest_end = u['end']
                            except Exception:
                                pass
                    # If this key has more recent annual data, pick it
                    if key_latest_end and (not best_latest_end or key_latest_end > best_latest_end):
                        best_latest_end = key_latest_end
                        best_key = rk
                        best_usd = usd

            logger.info(f"[SEC EDGAR Collector] Best GAAP revenue/premium key matched: '{best_key}' (latest end date: {best_latest_end})")

            revenue_val = None
            fiscal_year = None
            quarterly_revenue = []

            if best_key:
                annual_entries = []
                quarterly_entries = []
                for u in best_usd:
                    if 'start' not in u or 'end' not in u or 'val' not in u:
                        continue
                    try:
                        start = datetime.strptime(u['start'], "%Y-%m-%d")
                        end = datetime.strptime(u['end'], "%Y-%m-%d")
                        days = (end - start).days
                        if 330 <= days <= 390:
                            annual_entries.append(u)
                        elif 80 <= days <= 105:
                            quarterly_entries.append(u)
                    except Exception:
                        continue

                # 1. Extrapolate latest annual
                if annual_entries:
                    latest_annual = sorted(annual_entries, key=lambda x: (x.get('end', ''), x.get('filed', '')))[-1]
                    revenue_val = latest_annual['val']
                    try:
                        fiscal_year = int(latest_annual['end'].split('-')[0])
                    except Exception:
                        fiscal_year = latest_annual.get('fy')
                    logger.info(f"[SEC EDGAR Collector] Extracted annual revenue: {revenue_val} for fiscal year {fiscal_year}")

                # 2. Extrapolate quarterly revenues (sorted chronologically and deduplicated by end date)
                if quarterly_entries:
                    sorted_quarters = sorted(quarterly_entries, key=lambda x: (x.get('end', ''), x.get('filed', '')))
                    dedup_quarters = {}
                    for q in sorted_quarters:
                        dedup_quarters[q['end']] = q['val']
                    
                    chronological_ends = sorted(dedup_quarters.keys())
                    quarterly_revenue = [dedup_quarters[e] for e in chronological_ends]
                    logger.info(f"[SEC EDGAR Collector] Extracted quarterly revenues: {quarterly_revenue}")

            # Fetch submissions to count subsidiaries if Exhibit 21 is available
            subsidiaries_count = 0
            business_text = ""
            risk_text = ""
            mdna_text = ""
            segment_text = ""
            try:
                submissions_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
                logger.info(f"[SEC EDGAR Collector] Requesting submissions URL: {submissions_url}")
                req_sub = urllib.request.Request(submissions_url, headers={'User-Agent': self.USER_AGENT})
                with urllib.request.urlopen(req_sub, timeout=10) as res_sub:
                    resp_sub_bytes = res_sub.read()
                    logger.info(f"[SEC EDGAR Collector] Submissions response size: {len(resp_sub_bytes)} bytes")
                    sub_data = json.loads(resp_sub_bytes.decode())
                
                filings = sub_data.get('filings', {}).get('recent', {})
                forms = filings.get('form', [])
                accessions = filings.get('accessionNumber', [])
                
                acc_no = None
                for i, f in enumerate(forms):
                    if f == '10-K':
                        acc_no = accessions[i]
                        break
                        
                if acc_no:
                    acc_no_nodashes = acc_no.replace('-', '')
                    index_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_no_nodashes}/index.json"
                    logger.info(f"[SEC EDGAR Collector] Requesting index directory: {index_url}")
                    req_idx = urllib.request.Request(index_url, headers={'User-Agent': self.USER_AGENT})
                    with urllib.request.urlopen(req_idx, timeout=10) as res_idx:
                        idx = json.loads(res_idx.read().decode())
                        
                    ex21_file = None
                    primary_doc = None
                    for file_info in idx['directory']['item']:
                        name = file_info['name']
                        lower_name = name.lower()
                        if 'ex21' in lower_name or 'ex-21' in lower_name or 'exhibit21' in lower_name:
                            ex21_file = name
                        elif lower_name.endswith('.htm') and 'ex' not in lower_name and not primary_doc:
                            primary_doc = name
                            
                    if ex21_file:
                        file_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_no_nodashes}/{ex21_file}"
                        logger.info(f"[SEC EDGAR Collector] Requesting Exhibit 21 URL: {file_url}")
                        req_file = urllib.request.Request(file_url, headers={'User-Agent': self.USER_AGENT})
                        with urllib.request.urlopen(req_file, timeout=10) as res_file:
                            html = res_file.read().decode('utf-8', errors='ignore')
                        
                        import re
                        rows = re.findall(r'<tr[^>]*>', html, re.IGNORECASE)
                        subsidiaries_count = max(0, len(rows) - 1)
                        logger.info(f"[SEC EDGAR Collector] Counted {subsidiaries_count} subsidiaries in Exhibit 21.")

                    if primary_doc:
                        file_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_no_nodashes}/{primary_doc}"
                        logger.info(f"[SEC EDGAR Collector] Requesting primary 10-K filing URL: {file_url}")
                        req_file = urllib.request.Request(file_url, headers={'User-Agent': self.USER_AGENT})
                        with urllib.request.urlopen(req_file, timeout=10) as res_file:
                            html_10k = res_file.read().decode('utf-8', errors='ignore')
                            
                        import re
                        text_10k = re.sub(r'<[^>]+>', ' ', html_10k)
                        text_10k = re.sub(r'\s+', ' ', text_10k)
                        
                        m_bus = re.search(r'(?i)Item\s+1\.\s+Business\b(.*?)(?:Item\s+1A|Item\s+2)', text_10k)
                        if m_bus:
                            business_text = m_bus.group(1)[:4000]
                            logger.info(f"[SEC EDGAR Collector] Extracted Item 1 Business ({len(business_text)} chars)")
                        
                        m_risk = re.search(r'(?i)Item\s+1A\.\s+Risk Factors\b(.*?)(?:Item\s+1B|Item\s+2)', text_10k)
                        if m_risk:
                            risk_text = m_risk.group(1)[:4000]
                            logger.info(f"[SEC EDGAR Collector] Extracted Item 1A Risk Factors ({len(risk_text)} chars)")
                        
                        m_mdna = re.search(r'(?i)Item\s+7\.\s+Management\'s Discussion(.*?)(?:Item\s+7A|Item\s+8)', text_10k)
                        if m_mdna:
                            mdna_text = m_mdna.group(1)[:4000]
                            logger.info(f"[SEC EDGAR Collector] Extracted Item 7 MD&A ({len(mdna_text)} chars)")
                        
                        m_seg = re.search(r'(?i)(?:Segment Reporting|Reportable Segments)(.{0,2000})', text_10k)
                        if m_seg:
                            segment_text = m_seg.group(1)
                            logger.info(f"[SEC EDGAR Collector] Extracted Segment Reporting indicator text ({len(segment_text)} chars)")
            except Exception as e:
                import traceback
                logger.error(f"[SEC EDGAR Collector] Submissions or 10-K text extraction failed: {e}\n{traceback.format_exc()}")

            raw_sec_context = {
                "cik": cik,
                "matched_entity_name": matched_name,
                "raw_annual_revenue": revenue_val,
                "fiscal_year": fiscal_year,
                "exhibit21_subsidiaries_count": subsidiaries_count,
                "quarterly_revenue": quarterly_revenue,
                "business_section": business_text,
                "risk_factors_section": risk_text,
                "mda_section": mdna_text,
                "segment_reporting": segment_text
            }

            # Call LLM to parse and extract target fields
            prompt_vars = {
                "company_name": company_name,
                "domain": domain,
                "sec_text": json.dumps(raw_sec_context)
            }
            prompt = self.format_prompt(self.config.prompt_template, **prompt_vars)
            response_text = self.call_llm(prompt)
            extracted = self.parse_json(response_text)
            
            findings = {k: extracted.get(k) for k in self.config.target_fields}
            findings["quarterly_revenue"] = quarterly_revenue
            logger.info(f"[SEC EDGAR Collector] Target mapped findings: {findings}")
            return {
                "source": self.config.source_name,
                "status": "success",
                "findings": findings
            }
        except Exception as e:
            import traceback
            logger.error(f"[SEC EDGAR Collector] Collection failed: {e}\n{traceback.format_exc()}")
            return {
                "source": self.config.source_name,
                "status": "error",
                "message": f"{e}\nTraceback:\n{traceback.format_exc()}",
                "findings": {}
            }

class DNBCollectorAgent(BaseCollectorAgent):
    USER_AGENT = 'CyberRiskInsurancePOC/1.0 (https://github.com/ShivamModi09/CyberRiskInsurance)'

    async def collect(self, company_name: str, domain: str) -> Dict[str, Any]:
        logger = self.get_logger()
        query = urllib.parse.quote(company_name)
        url = f"https://api.gleif.org/api/v1/fuzzycompletions?field=entity.legalName&q={query}"
        logger.info(f"[GLEIF DNB Collector] Resolving legal entity fuzzy completion URL: {url}")
        
        try:
            req = urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': self.USER_AGENT})
            with urllib.request.urlopen(req, timeout=5) as response:
                resp_bytes = response.read()
                logger.info(f"[GLEIF DNB Collector] Received response size: {len(resp_bytes)} bytes")
                data = json.loads(resp_bytes.decode())
                
            if data.get("data") and len(data["data"]) > 0:
                entity = data["data"][0].get("attributes", {}).get("entity", {})
                logger.info(f"[GLEIF DNB Collector] Matched GLEIF Entity attributes: {json.dumps(entity)}")
                
                # Pass GLEIF raw structure to LLM
                prompt_vars = {
                    "company_name": company_name,
                    "domain": domain,
                    "dnb_text": json.dumps(entity)
                }
                prompt = self.format_prompt(self.config.prompt_template, **prompt_vars)
                response_text = self.call_llm(prompt)
                extracted = self.parse_json(response_text)
                
                findings = {k: extracted.get(k) for k in self.config.target_fields}
                logger.info(f"[GLEIF DNB Collector] Mapped target fields: {findings}")
                return {
                    "source": self.config.source_name,
                    "status": "success",
                    "findings": findings
                }
            else:
                logger.info(f"[GLEIF DNB Collector] No company matches resolved in GLEIF index for query '{company_name}'")
                return {
                    "source": self.config.source_name,
                    "status": "skipped",
                    "message": "No company legal entity matched in GLEIF registration database.",
                    "findings": {}
                }
        except Exception as e:
            import traceback
            logger.error(f"[GLEIF DNB Collector] Collection failed: {e}\n{traceback.format_exc()}")
            return {
                "source": self.config.source_name,
                "status": "error",
                "message": f"{e}\nTraceback:\n{traceback.format_exc()}",
                "findings": {}
            }

class DomainScraperCollectorAgent(BaseCollectorAgent):

    async def collect(self, company_name: str, domain: str) -> Dict[str, Any]:
        import re
        import asyncio
        logger = self.get_logger()
        logger.info(f"[Domain Scraper Collector] Starting recursive collection for '{company_name}' on domain '{domain}'")

        # 1. Brand Keywords Extraction
        words = re.findall(r'[a-zA-Z0-9]+', company_name.lower())
        ignored_suffixes = {"inc", "corp", "corporation", "ltd", "limited", "co", "llc", "group", "pc", "intl", "international", "incorporated", "llp", "company", "plc"}
        brand_keywords = [w for w in words if w not in ignored_suffixes and len(w) > 2]
        if not brand_keywords:
            brand_keywords = [w for w in words if len(w) > 1]
            
        logger.info(f"[Domain Scraper Collector] Brand keywords: {brand_keywords}")

        # 2. Helpers for SSL, crt.sh query, and URL fetching
        async def check_ssl(domain_str: str) -> bool:
            def blocking_ssl_check():
                try:
                    context = ssl.create_default_context()
                    with socket.create_connection((domain_str, 443), timeout=3) as sock:
                        with context.wrap_socket(sock, server_hostname=domain_str) as ssock:
                            ssock.getpeercert()
                            return True
                except Exception:
                    return False
            return await asyncio.to_thread(blocking_ssl_check)

        async def discover_crtsh(domain_str: str) -> set:
            def blocking_query():
                subdomains = set()
                try:
                    query_url = f"https://crt.sh/?q={urllib.parse.quote(domain_str)}&output=json"
                    req = urllib.request.Request(query_url, headers={'User-Agent': 'CyberRiskInsurancePOC/1.0'})
                    with urllib.request.urlopen(req, timeout=4) as response:
                        data = json.loads(response.read().decode('utf-8'))
                        for entry in data:
                            name_value = entry.get("name_value", "")
                            for name in name_value.split("\n"):
                                name = name.strip().lower()
                                if name.startswith("*."):
                                    name = name[2:]
                                if name:
                                    subdomains.add(name)
                except Exception as e:
                    logger.info(f"[Domain Scraper Collector] crt.sh query failed for {domain_str}: {e}")
                return subdomains
            return await asyncio.to_thread(blocking_query)

        async def scrape_url(url_str: str) -> tuple[str, set[str]]:
            def blocking_fetch():
                text = ""
                links = set()
                try:
                    req = urllib.request.Request(url_str, headers={'User-Agent': 'CyberRiskInsurancePOC/1.0'})
                    with urllib.request.urlopen(req, timeout=4) as response:
                        page_bytes = response.read()
                        page_html = page_bytes.decode('utf-8', errors='ignore')
                        
                        # Extract absolute domains from link tags
                        found_domains = re.findall(r'https?://([a-zA-Z0-9.-]+)', page_html)
                        for d in found_domains:
                            d = d.lower()
                            if d.startswith("www."):
                                d = d[4:]
                            if d:
                                links.add(d)

                        # Clean HTML tags and scripts
                        cleaned = re.sub(r'<style.*?>.*?</style>', ' ', page_html, flags=re.DOTALL | re.IGNORECASE)
                        cleaned = re.sub(r'<script.*?>.*?</script>', ' ', cleaned, flags=re.DOTALL | re.IGNORECASE)
                        cleaned = re.sub(r'<[^>]+>', ' ', cleaned)
                        cleaned = re.sub(r'\s+', ' ', cleaned)
                        text = cleaned
                except Exception as e:
                    logger.info(f"[Domain Scraper Collector] Fetch failed for {url_str}: {e}")
                return text, links
            return await asyncio.to_thread(blocking_fetch)

        # 3. Filtering Helper
        def is_valid_domain(candidate: str) -> bool:
            candidate = candidate.lower()
            # Rule A: Subdomain of primary domain
            if candidate == domain.lower() or candidate.endswith("." + domain.lower()):
                return True
            # Rule B: Alternate domain matching brand keywords
            for keyword in brand_keywords:
                if keyword in candidate:
                    return True
            return False

        discovered_domains = {domain.lower()}
        crawled_domains = set()
        domain_ssl_status = {}

        # Stage 1: SSL Check and Page Crawl for Primary Domain + crt.sh Discovery
        primary_ssl = await check_ssl(domain)
        domain_ssl_status[domain.lower()] = primary_ssl

        protocol = "https" if primary_ssl else "http"
        primary_paths = ["", "/about", "/services", "/solutions", "/products", "/platform"]
        primary_urls = [f"{protocol}://{domain.lower()}{p}" for p in primary_paths]

        logger.info(f"[Domain Scraper Collector] Stage 1: Scraping primary domain and querying crt.sh...")
        stage1_tasks = [scrape_url(url) for url in primary_urls]
        stage1_tasks.append(discover_crtsh(domain))

        stage1_results = await asyncio.gather(*stage1_tasks)

        primary_pages_results = stage1_results[:-1]
        crtsh_subdomains = stage1_results[-1]

        merged_text = ""
        seen_lines = set()
        all_discovered_links = set(crtsh_subdomains)

        for text, links in primary_pages_results:
            all_discovered_links.update(links)
            if text:
                chunks = text.split('.')
                for c in chunks:
                    c = c.strip()
                    if len(c) > 15 and c not in seen_lines:
                        seen_lines.add(c)
                        merged_text += c + ". "

        crawled_domains.add(domain.lower())

        # Stage 2: Filter and Limit Discovered Subdomains / Alternate Domains
        candidates = [link for link in all_discovered_links if link not in crawled_domains and is_valid_domain(link)]
        # Cap to a maximum of 7 additional domains (making it 8 total)
        candidates = candidates[:7]

        logger.info(f"[Domain Scraper Collector] Discovered valid domain candidates: {candidates}")

        if candidates:
            # Perform parallel SSL checks
            ssl_checks = await asyncio.gather(*[check_ssl(cand) for cand in candidates])
            for cand, ssl_ok in zip(candidates, ssl_checks):
                domain_ssl_status[cand] = ssl_ok
                discovered_domains.add(cand)

            # Build URLs (crawling "/" and "/about" for each candidate)
            cand_urls = []
            for cand in candidates:
                proto = "https" if domain_ssl_status[cand] else "http"
                cand_urls.append((cand, f"{proto}://{cand}"))
                cand_urls.append((cand, f"{proto}://{cand}/about"))

            logger.info(f"[Domain Scraper Collector] Stage 2: Crawling candidate pages in parallel...")
            cand_scrape_results = await asyncio.gather(*[scrape_url(url) for _, url in cand_urls])

            for (_, url), (text, links) in zip(cand_urls, cand_scrape_results):
                if text:
                    chunks = text.split('.')
                    for c in chunks:
                        c = c.strip()
                        if len(c) > 15 and c not in seen_lines:
                            seen_lines.add(c)
                            merged_text += c + ". "

        # Stage 3: Construct context and call LLM
        domain_objects = [{"url": d, "https_encrypted": domain_ssl_status.get(d, False)} for d in discovered_domains]
        merged_text = merged_text[:15000]

        raw_context = {
            "url": domain,
            "https_encrypted": primary_ssl,
            "discovered_domains": domain_objects,
            "homepage_html_snippet": merged_text
        }

        try:
            prompt_vars = {
                "company_name": company_name,
                "domain": domain,
                "scraper_text": json.dumps(raw_context)
            }
            prompt = self.format_prompt(self.config.prompt_template, **prompt_vars)
            response_text = self.call_llm(prompt)
            extracted = self.parse_json(response_text)

            findings = {k: extracted.get(k) for k in self.config.target_fields}

            # Hard override verified domains list
            if "domains" in findings:
                findings["domains"] = domain_objects

            logger.info(f"[Domain Scraper Collector] Mapped findings: {findings}")
            return {
                "source": self.config.source_name,
                "status": "success",
                "findings": findings
            }
        except Exception as e:
            import traceback
            logger.error(f"[Domain Scraper Collector] Collection failed: {e}\n{traceback.format_exc()}")
            return {
                "source": self.config.source_name,
                "status": "error",
                "message": f"{e}\nTraceback:\n{traceback.format_exc()}",
                "findings": {
                    "domains": domain_objects
                }
            }


class ResponsesAPICollectorAgent(BaseCollectorAgent):
    async def collect(self, company_name: str, domain: str) -> Dict[str, Any]:
        # Production Responses API connector stub - skips if environment configuration is off
        if os.environ.get("ENABLE_RESPONSES_API", "false").lower() != "true":
            return {
                "source": self.config.source_name,
                "status": "skipped",
                "findings": {}
            }
        # Otherwise placeholder returns empty findings
        return {
            "source": self.config.source_name,
            "status": "success",
            "findings": {}
        }

class WebSearchCollectorAgent(BaseCollectorAgent):
    async def collect(self, company_name: str, domain: str) -> Dict[str, Any]:
        # WebSearch is currently marked as 'future' in rule configurations and disabled.
        return {
            "source": self.config.source_name,
            "status": "skipped",
            "message": "WebSearch API key not configured.",
            "findings": {}
        }
