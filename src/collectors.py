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
        
        try:
            req = urllib.request.Request(search_url, headers={'User-Agent': self.USER_AGENT})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                
            search_results = data.get("query", {}).get("search", [])
            if not search_results:
                return {
                    "source": self.config.source_name,
                    "status": "skipped",
                    "message": "No Wikipedia article found.",
                    "findings": {}
                }
                
            title = urllib.parse.quote(search_results[0]["title"])
            # Fetch full article (no exintro) with plain text to capture acquisitions, global ops, etc.
            summary_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=&titles={title}&format=json"
            
            req2 = urllib.request.Request(summary_url, headers={'User-Agent': self.USER_AGENT})
            with urllib.request.urlopen(req2, timeout=10) as response2:
                summary_data = json.loads(response2.read().decode())
            
            pages = summary_data.get("query", {}).get("pages", {})
            page = list(pages.values())[0] if pages else {}
            # Cap at 12000 chars to keep LLM prompt within safe token limits
            extract = page.get("extract", "")[:12000]
            
            if not extract:
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
            return {
                "source": self.config.source_name,
                "status": "success",
                "findings": findings
            }
        except Exception as e:
            return {
                "source": self.config.source_name,
                "status": "error",
                "message": str(e),
                "findings": {}
            }

class WikidataCollectorAgent(BaseCollectorAgent):
    USER_AGENT = 'CyberRiskInsurancePOC/1.0 (https://github.com/ShivamModi09/CyberRiskInsurance)'

    async def collect(self, company_name: str, domain: str) -> Dict[str, Any]:
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
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                
            search_results = data.get('search', [])
            if not search_results:
                return {
                    "source": self.config.source_name,
                    "status": "skipped",
                    "message": "No entity resolved on Wikidata.",
                    "findings": {}
                }
                
            qids = [res['id'] for res in search_results]
            
            # 2. Get entity claims
            query2 = urllib.parse.urlencode({
                'action': 'wbgetentities',
                'ids': '|'.join(qids),
                'format': 'json',
                'props': 'claims|labels'
            })
            url2 = f'https://www.wikidata.org/w/api.php?{query2}'
            req2 = urllib.request.Request(url2, headers={'User-Agent': self.USER_AGENT})
            
            with urllib.request.urlopen(req2, timeout=10) as response:
                data2 = json.loads(response.read().decode())
                
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
                if domain_match or sim > 0.8:
                    best_qid = qid_candidate
                    best_claims = candidate_claims
                    break
                    
            if not best_qid:
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
            # P31 = instance of (e.g. insurance company, mutual company)
            instance_of = extract_claim_values('P31')
            # P166 = award received / P749 = parent organization
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
            return {
                "source": self.config.source_name,
                "status": "success",
                "findings": findings
            }
        except Exception as e:
            return {
                "source": self.config.source_name,
                "status": "error",
                "message": str(e),
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
        import re
        import difflib

        encoded = urllib.parse.quote(f'"{company_name}"')

        # --- Tier 1: EDGAR EFTS full-text search (handles private companies) ---
        try:
            search_url = f"https://efts.sec.gov/LATEST/search-index?q={encoded}&forms=10-K&hits.hits.total.value=true"
            req = urllib.request.Request(search_url, headers={'User-Agent': self.USER_AGENT})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())

            hits = data.get('hits', {}).get('hits', [])
            if hits:
                # Score hits by name similarity, pick best match
                best_cik = None
                best_name = None
                best_score = 0.0
                for hit in hits[:10]:
                    src = hit.get('_source', {})
                    entity_name = src.get('entity_name', '')
                    # CIK is the first 10 chars of the accession number (_id)
                    acc_id = hit.get('_id', '')
                    raw_cik = acc_id.split('-')[0] if '-' in acc_id else acc_id[:10]
                    if not raw_cik.isdigit():
                        continue
                    score = difflib.SequenceMatcher(None, company_name.lower(), entity_name.lower()).ratio()
                    if score > best_score:
                        best_score = score
                        best_cik = raw_cik.zfill(10)
                        best_name = entity_name
                if best_cik and best_score > 0.4:
                    return best_cik, best_name
        except Exception:
            pass

        # --- Tier 2: EDGAR company browse API (wider net, parses XML atom feed) ---
        try:
            browse_name = urllib.parse.quote(company_name)
            browse_url = f"https://www.sec.gov/cgi-bin/browse-edgar?company={browse_name}&CIK=&type=10-K&dateb=&owner=include&count=10&search_text=&action=getcompany&output=atom"
            req2 = urllib.request.Request(browse_url, headers={'User-Agent': self.USER_AGENT})
            with urllib.request.urlopen(req2, timeout=10) as resp2:
                xml_text = resp2.read().decode()

            # Extract CIK from atom XML: <company-info><CIK>...</CIK><conformed-name>...</conformed-name>
            cik_matches = re.findall(r'<CIK>(\d+)</CIK>', xml_text)
            name_matches = re.findall(r'<conformed-name>(.*?)</conformed-name>', xml_text, re.IGNORECASE)
            if cik_matches and name_matches:
                # Pick best name match
                best_cik = None
                best_name = None
                best_score = 0.0
                for cik_val, nm in zip(cik_matches, name_matches):
                    score = difflib.SequenceMatcher(None, company_name.lower(), nm.lower()).ratio()
                    if score > best_score:
                        best_score = score
                        best_cik = str(cik_val).zfill(10)
                        best_name = nm
                if best_cik and best_score > 0.3:
                    return best_cik, best_name
        except Exception:
            pass

        # --- Tier 3: Fallback — company_tickers.json (public/ticker companies) ---
        try:
            req3 = urllib.request.Request("https://www.sec.gov/files/company_tickers.json", headers={'User-Agent': self.USER_AGENT})
            with urllib.request.urlopen(req3, timeout=10) as resp3:
                tickers = json.loads(resp3.read().decode())
            for _, data in tickers.items():
                if company_name.lower() in data['title'].lower():
                    return str(data['cik_str']).zfill(10), data['title']
        except Exception:
            pass

        return None, None

    async def collect(self, company_name: str, domain: str) -> Dict[str, Any]:
        try:
            # 1. Resolve Company Name to CIK via multi-tier EDGAR name search
            cik, matched_name = self._resolve_cik(company_name)

            if not cik:
                return {
                    "source": self.config.source_name,
                    "status": "skipped",
                    "message": f"Company '{company_name}' not found in SEC EDGAR (tried EFTS search, browse API, and tickers list).",
                    "findings": {}
                }

            # 2. Fetch Company Facts
            req2 = urllib.request.Request(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json", headers={'User-Agent': self.USER_AGENT})
            with urllib.request.urlopen(req2, timeout=10) as response:
                facts = json.loads(response.read().decode())
                
            gaap = facts.get('facts', {}).get('us-gaap', {})
            
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
                    # Use end date's year as the fiscal year if fy is missing or comparative-labeled incorrectly
                    try:
                        fiscal_year = int(latest_annual['end'].split('-')[0])
                    except Exception:
                        fiscal_year = latest_annual.get('fy')

                # 2. Extrapolate quarterly revenues (sorted chronologically and deduplicated by end date)
                if quarterly_entries:
                    sorted_quarters = sorted(quarterly_entries, key=lambda x: (x.get('end', ''), x.get('filed', '')))
                    dedup_quarters = {}
                    for q in sorted_quarters:
                        dedup_quarters[q['end']] = q['val']
                    
                    # Sort the unique keys chronologically
                    chronological_ends = sorted(dedup_quarters.keys())
                    quarterly_revenue = [dedup_quarters[e] for e in chronological_ends]

            # Fetch submissions to count subsidiaries if Exhibit 21 is available
            subsidiaries_count = 0
            business_text = ""
            risk_text = ""
            mdna_text = ""
            segment_text = ""
            try:
                req_sub = urllib.request.Request(f"https://data.sec.gov/submissions/CIK{cik}.json", headers={'User-Agent': self.USER_AGENT})
                with urllib.request.urlopen(req_sub, timeout=10) as res_sub:
                    sub_data = json.loads(res_sub.read().decode())
                
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
                        req_file = urllib.request.Request(file_url, headers={'User-Agent': self.USER_AGENT})
                        with urllib.request.urlopen(req_file, timeout=10) as res_file:
                            html = res_file.read().decode('utf-8', errors='ignore')
                        
                        import re
                        rows = re.findall(r'<tr[^>]*>', html, re.IGNORECASE)
                        subsidiaries_count = max(0, len(rows) - 1)

                    business_text = ""
                    risk_text = ""
                    mdna_text = ""
                    segment_text = ""
                    
                    if primary_doc:
                        file_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_no_nodashes}/{primary_doc}"
                        req_file = urllib.request.Request(file_url, headers={'User-Agent': self.USER_AGENT})
                        with urllib.request.urlopen(req_file, timeout=10) as res_file:
                            html_10k = res_file.read().decode('utf-8', errors='ignore')
                            
                        import re
                        # Strip HTML
                        text_10k = re.sub(r'<[^>]+>', ' ', html_10k)
                        text_10k = re.sub(r'\s+', ' ', text_10k)
                        
                        # Find Item 1. Business
                        m_bus = re.search(r'(?i)Item\s+1\.\s+Business\b(.*?)(?:Item\s+1A|Item\s+2)', text_10k)
                        if m_bus: business_text = m_bus.group(1)[:4000]
                        
                        # Find Item 1A. Risk Factors
                        m_risk = re.search(r'(?i)Item\s+1A\.\s+Risk Factors\b(.*?)(?:Item\s+1B|Item\s+2)', text_10k)
                        if m_risk: risk_text = m_risk.group(1)[:4000]
                        
                        # Find Item 7. MD&A
                        m_mdna = re.search(r'(?i)Item\s+7\.\s+Management\'s Discussion(.*?)(?:Item\s+7A|Item\s+8)', text_10k)
                        if m_mdna: mdna_text = m_mdna.group(1)[:4000]
                        
                        # Find Segment Reporting
                        m_seg = re.search(r'(?i)(?:Segment Reporting|Reportable Segments)(.{0,2000})', text_10k)
                        if m_seg: segment_text = m_seg.group(1)
            except Exception:
                pass

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
            # Direct override to bypass LLM parsing/truncation errors
            findings["quarterly_revenue"] = quarterly_revenue
            return {
                "source": self.config.source_name,
                "status": "success",
                "findings": findings
            }
        except Exception as e:
            return {
                "source": self.config.source_name,
                "status": "error",
                "message": str(e),
                "findings": {}
            }

class DNBCollectorAgent(BaseCollectorAgent):
    USER_AGENT = 'CyberRiskInsurancePOC/1.0 (https://github.com/ShivamModi09/CyberRiskInsurance)'

    async def collect(self, company_name: str, domain: str) -> Dict[str, Any]:
        # Connects to GLEIF API as DNB database resolver
        query = urllib.parse.quote(company_name)
        url = f"https://api.gleif.org/api/v1/fuzzycompletions?field=entity.legalName&q={query}"
        
        try:
            req = urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': self.USER_AGENT})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                
            if data.get("data") and len(data["data"]) > 0:
                entity = data["data"][0].get("attributes", {}).get("entity", {})
                
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
                return {
                    "source": self.config.source_name,
                    "status": "success",
                    "findings": findings
                }
            else:
                return {
                    "source": self.config.source_name,
                    "status": "skipped",
                    "message": "No company legal entity matched in GLEIF registration database.",
                    "findings": {}
                }
        except Exception as e:
            return {
                "source": self.config.source_name,
                "status": "error",
                "message": str(e),
                "findings": {}
            }

class DomainScraperCollectorAgent(BaseCollectorAgent):
    USER_AGENT = 'CyberRiskInsurancePOC/1.0 (https://github.com/ShivamModi09/CyberRiskInsurance)'
    CRTSH_URL = 'https://crt.sh/?q={query}&output=json'

    def _check_ssl(self, host: str) -> bool:
        """Check if the host supports HTTPS via SSL handshake."""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((host, 443), timeout=4) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    ssock.getpeercert()
                    return True
        except Exception:
            return False

    def _is_reachable(self, host: str) -> bool:
        """Check if the host is reachable on port 80 or 443."""
        for port in (443, 80):
            try:
                with socket.create_connection((host, port), timeout=4):
                    return True
            except Exception:
                continue
        return False

    def _crtsh_discover(self, root_domain: str) -> list:
        """
        Query crt.sh Certificate Transparency logs to discover all real subdomains
        that have ever had an SSL certificate issued for this root domain.
        Returns a deduplicated list of host strings.
        """
        import re
        # Strip leading www. to get bare root domain for wildcard query
        base = re.sub(r'^www\.', '', root_domain)
        query = urllib.parse.quote(f'%.{base}')
        url = self.CRTSH_URL.format(query=query)
        discovered = set()
        # Always include the input domain itself
        discovered.add(root_domain)

        try:
            req = urllib.request.Request(url, headers={'User-Agent': self.USER_AGENT})
            with urllib.request.urlopen(req, timeout=10) as response:
                entries = json.loads(response.read().decode())
            for entry in entries:
                name = entry.get('name_value', '').strip().lower()
                # name_value can be newline-separated or contain wildcards
                for part in name.split('\n'):
                    part = part.strip()
                    # Skip wildcard entries and entries for different roots
                    if part.startswith('*') or not part.endswith(base):
                        continue
                    if part and re.match(r'^[a-z0-9._-]+$', part):
                        discovered.add(part)
        except Exception:
            pass  # crt.sh unavailable — fall back to just the provided domain

        return list(discovered)

    def _scrape_domain(self, host: str, ssl_valid: bool) -> tuple:
        """
        Scrape key pages from a single domain. Returns (text_content, is_reachable).
        """
        import re
        paths = ["", "/about", "/services", "/solutions", "/products",
                 "/platform", "/business", "/commercial", "/corporate"]
        protocol = "https" if ssl_valid else "http"
        merged_text = ""
        seen_lines = set()
        reached = False

        for path in paths:
            try:
                url = f"{protocol}://{host}{path}"
                req = urllib.request.Request(url, headers={'User-Agent': self.USER_AGENT})
                with urllib.request.urlopen(req, timeout=5) as response:
                    page_html = response.read().decode('utf-8', errors='ignore')
                    reached = True

                    text = re.sub(r'<style.*?>.*?</style>', ' ', page_html, flags=re.DOTALL | re.IGNORECASE)
                    text = re.sub(r'<script.*?>.*?</script>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
                    text = re.sub(r'<[^>]+>', ' ', text)
                    text = re.sub(r'\s+', ' ', text)

                    chunks = text.split('.')
                    for c in chunks:
                        c = c.strip()
                        if len(c) > 15 and c not in seen_lines:
                            seen_lines.add(c)
                            merged_text += c + ". "
            except Exception:
                pass

        return merged_text, reached

    async def collect(self, company_name: str, domain: str) -> Dict[str, Any]:
        # Accept all_domains from the agent's state context if available (set by CLI multi-domain input)
        # The base class passes the full state; fall back to single domain if not available.
        all_input_domains = getattr(self, '_state_all_domains', [domain])

        # 1. For each input root domain, discover subdomains via crt.sh
        all_candidates = []
        seen_candidates = set()
        for root in all_input_domains:
            for host in self._crtsh_discover(root):
                if host not in seen_candidates:
                    seen_candidates.add(host)
                    all_candidates.append(host)

        # 2. Probe each candidate — check reachability and SSL
        reachable_domains = []
        all_merged_text = ""
        seen_text_lines: set = set()

        for host in all_candidates:
            if not self._is_reachable(host):
                continue  # skip unreachable hosts silently
            ssl_valid = self._check_ssl(host)
            page_text, reached = self._scrape_domain(host, ssl_valid)

            if reached:
                reachable_domains.append({"url": host, "https_encrypted": ssl_valid})
                for chunk in page_text.split(". "):
                    chunk = chunk.strip()
                    if len(chunk) > 15 and chunk not in seen_text_lines:
                        seen_text_lines.add(chunk)
                        all_merged_text += chunk + ". "

        # If nothing was reachable at all, fallback to primary domain only
        if not reachable_domains:
            ssl_primary = self._check_ssl(domain)
            reachable_domains = [{"url": domain, "https_encrypted": ssl_primary}]

        # Cap merged text for LLM
        all_merged_text = all_merged_text[:14000]

        raw_context = {
            "primary_domain": domain,
            "all_input_domains": all_input_domains,
            "discovered_domains": reachable_domains,
            "https_encrypted": any(d["https_encrypted"] for d in reachable_domains),
            "homepage_html_snippet": all_merged_text
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
            # Hard override: always report the full verified domain list
            findings["domains"] = reachable_domains

            return {
                "source": self.config.source_name,
                "status": "success",
                "findings": findings
            }
        except Exception as e:
            return {
                "source": self.config.source_name,
                "status": "error",
                "message": str(e),
                "findings": {
                    "domains": reachable_domains
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
