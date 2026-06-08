from typing import Dict, Any
from src.state import CyberRiskState
from src.utils.cache_manager import CacheManager

# Hardcoded mismatch detection signals
WRONG_ENTITY_KEYWORDS = {
    "amazon": ["river", "forest", "rainforest"],
    "apple": ["fruit", "orchard", "pie", "cider"],
    "microsoft": ["microbiology", "softball"],
}

# Domain aliases for well-known companies that may not match by name-slug alone
DOMAIN_ALIASES = {
    "tcs": "tcs.com",
    "tata consultancy services": "tcs.com",
    "alphabet": "google.com",
    "meta": "meta.com",
}

def supervisor_node(state: CyberRiskState) -> Dict[str, Any]:
    name = state.get("company_name", "").strip()
    domain = state.get("domain", "").strip()
    
    logs = []
    logs.append(f"Supervisor: Validating input - Name: '{name}', Domain: '{domain}'")
    
    # 1. Validation check
    if not name or not domain or "." not in domain:
        logs.append("Supervisor Reject: Invalid company name or domain format.")
        return {
            "valid": False,
            "mismatch_flag": False,
            "entity_status": "Unvalidated",
            "entity_resolution_confidence": "Low",
            "cache_hit": False,
            "enrichment": {},
            "audit_logs": state.get("audit_logs", []) + logs
        }
        
    # 2. Enrich Domain / Country & TLD
    tld = domain.split(".")[-1].lower()
    country = "USA"  # Default
    if tld == "ca":
        country = "Canada"
    elif tld == "uk":
        country = "UK"
    elif tld == "de":
        country = "Germany"
    elif tld == "in":
        country = "India"
        
    enrichment = {
        "tld": tld,
        "country_detected": country
    }
    logs.append(f"Supervisor: Enriched TLD: '{tld}', Detected Country: '{country}'")

    # 3. Mismatch Detection
    mismatch_flag = False
    entity_status = "Match"
    entity_resolution_confidence = "High"  # Default - optimistic

    name_lower = name.lower()
    domain_lower = domain.lower()
    name_slug = name_lower.replace(" ", "").replace(",", "").replace(".", "")
    expected_domain = name_slug

    # Step 1: Check WRONG_ENTITY_KEYWORDS first — most specific signal
    for keyword, wrong_indicators in WRONG_ENTITY_KEYWORDS.items():
        if keyword in name_lower:
            for indicator in wrong_indicators:
                if indicator in domain_lower:
                    mismatch_flag = True
                    entity_status = "Mismatch"
                    entity_resolution_confidence = "Low"  # Bug 3 Fix
                    logs.append(
                        f"Supervisor Warning: Entity mismatch detected! Name has '{keyword}' "
                        f"but domain '{domain}' suggests '{indicator}'."
                    )
                    break

    if not mismatch_flag:
        # Step 2: Check domain aliases (e.g. TCS -> tcs.com)
        alias_domain = DOMAIN_ALIASES.get(name_lower)
        if alias_domain and alias_domain == domain_lower:
            entity_status = "Match"
            entity_resolution_confidence = "High"
            logs.append(f"Supervisor: Entity matched via domain alias '{alias_domain}'.")
        elif name_slug in domain_lower or any(
            part in domain_lower for part in name_lower.split() if len(part) > 3
        ):
            # Step 3: Slug / significant word match inside domain
            entity_status = "Match"
            entity_resolution_confidence = "High"
            logs.append(f"Supervisor: Entity name slug matches domain '{domain}'.")
        else:
            # Step 4: No match found — generic mismatch
            mismatch_flag = True
            entity_status = "Mismatch"
            entity_resolution_confidence = "Low"  # Bug 3 Fix
            logs.append(
                f"Supervisor Warning: Entity mismatch! Name '{name}' does not match domain '{domain}'."
            )

    # 4. Cache Lookup
    cache_mgr = CacheManager()
    cache_entry = cache_mgr.lookup(name, domain)
    cache_hit = cache_entry is not None
    
    collected_evidence_from_cache = {}
    if cache_hit:
        # New cache strategy: cache stores raw collected_evidence
        cached_evidence = cache_entry.get("collected_evidence", {})
        if cached_evidence:
            collected_evidence_from_cache = cached_evidence
            logs.append("Supervisor: Cache Hit! Restoring raw collector evidence for re-evaluation.")
        else:
            logs.append("Supervisor: Cache Hit! (Legacy format - no raw evidence). Will re-collect.")
            cache_hit = False  # Treat old format cache as a miss to force re-collection
            cache_entry = None
    else:
        logs.append("Supervisor: Cache Miss. Proceeding to collectors.")

    return {
        "valid": True,
        "enrichment": enrichment,
        "mismatch_flag": mismatch_flag,
        "entity_status": entity_status,
        "entity_resolution_confidence": entity_resolution_confidence,
        "cache_hit": cache_hit,
        "cache_data": cache_entry if cache_hit else None,
        # Restore raw evidence from cache so coordinator_node has data on a cache hit
        "collected_evidence": collected_evidence_from_cache if cache_hit else state.get("collected_evidence", {}),
        "audit_logs": state.get("audit_logs", []) + logs
    }
