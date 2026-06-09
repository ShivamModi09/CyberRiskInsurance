import os
import sys
import asyncio
import argparse
from src.registry import BusinessRuleRegistry
from src.workflows import build_cyber_risk_rating_graph
from src.cache import get_cache_manager

def print_header(title: str):
    print("\n" + "=" * 60)
    print(f" {title.upper()} ".center(60, "="))
    print("=" * 60)

async def main_async():
    # Load all rules to trigger registration
    import src.rules as _rules

    parser = argparse.ArgumentParser(description="Shared Agent Framework CLI")
    parser.add_argument("--list-rules", action="store_true", help="List all registered rules")
    parser.add_argument("--rule", type=str, help="Rule ID to run (e.g. cyber_risk_rating)")
    parser.add_argument("--company", type=str, help="Company name to evaluate")
    parser.add_argument("--domain", type=str, help="Company domain (e.g. techgiant.com)")
    
    args = parser.parse_args()

    if args.list_rules:
        print_header("Registered Rules")
        rules = BusinessRuleRegistry.list_rules()
        for r in rules:
            cfg = BusinessRuleRegistry.get(r)
            print(f"- {cfg.rule_id}: {cfg.rule_name} ({cfg.description})")
        sys.exit(0)

    if not args.rule or not args.company or not args.domain:
        parser.print_help()
        sys.exit(1)

    rule_id = args.rule.strip()
    company_name = args.company.strip()
    domain = args.domain.strip()

    if rule_id != "cyber_risk_rating":
        print(f"[ERROR] Rule ID '{rule_id}' is not supported in the active configuration.")
        sys.exit(1)

    print_header("Initializing Cyber Risk Predictor")
    print(f"Rule Target:    {rule_id}")
    print(f"Company Target: {company_name}")
    print(f"Primary Domain: {domain}")

    # Compile the LangGraph workflow
    app = build_cyber_risk_rating_graph(enable_cache=True)

    # Initial State
    initial_state = {
        "company_name": company_name,
        "domain": domain,
        "rule_id": rule_id,
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

    try:
        final_state = await app.ainvoke(initial_state)
    except Exception as e:
        print(f"\n[ERROR] Graph execution failed: {e}")
        sys.exit(1)

    # 1. Validation check
    if not final_state.get("valid"):
        print_header("Validation Failed")
        print("[REJECTED] The input company name or domain is invalid.")
        for log in final_state.get("audit_logs", []):
            print(f"  > {log}")
        sys.exit(0)

    # 2. Print Trace & Audit Logs
    print_header("Execution Trace & Logs")
    for log in final_state.get("audit_logs", []):
        print(f"  > {log}")

    # 3. Print Results
    evidence = final_state.get("collected_evidence", {})
    real_sources = []
    for tool_name, data in evidence.items():
        if data.get("status") == "success":
            real_sources.append(tool_name)

    print_header("Collectors Run")
    print("Real Sources Used:")
    print(f"{', '.join(real_sources) if real_sources else 'None'}")

    reconciled = final_state.get("reconciled_profile", {})
    print_header("Reconciled Company Profile")
    rev = reconciled.get('revenue')
    rev_display = f"${rev:,}" if rev is not None else "Not Available"
    print(f"Reconciled Revenue:   {rev_display}")
    print(f"Subsidiaries Count:   {len(reconciled.get('subsidiaries', []))}")
    print(f"Acquisitions Count:   {len(reconciled.get('acquisitions', []))}")
    print(f"Customer Type:        {reconciled.get('customer_type')}")
    print(f"E-commerce Platform:  {reconciled.get('has_ecommerce')}")
    print(f"Countries of Ops:     {', '.join(reconciled.get('countries_of_operation', []))}")
    print(f"Privacy Policy:       {reconciled.get('privacy_policy_published')}")

    print_header("Fact Checker Corroboration Claims")
    print(f"{'Underwriting Claim':<30} | {'Status':<15} | {'Source Count':<12}")
    print("-" * 65)
    for claim, info in final_state.get("claims_verification", {}).items():
        print(f"{claim:<30} | {info.get('status', 'Unsupported'):<15} | {info.get('sources_count', 0):<12}")

    print_header("Underwriter Modifier Evaluations")
    for idx, (mod, details) in enumerate(final_state.get("modifier_scores", {}).items(), 1):
        print(f"  {idx}. {mod}: {details.get('rating').upper()} (Score: {details.get('score')})")
        print(f"     Rationale: {final_state.get('underwriting_rationale', {}).get(mod)}")

    print_header("Final Underwriting Modifier Verdict")
    print(f"Entity Status:       {final_state.get('entity_status', 'Match')}")
    print(f"Risk Category:       {final_state.get('risk_category', 'Average').upper()}")
    print(f"Underwriting Score:  {final_state.get('confidence_score')}%")
    print(f"Confidence Band:     {final_state.get('confidence_band')}")
    print(f"Human Escalation:    {final_state.get('human_escalation_flag')}")

    # Write Cache on success
    if final_state.get("valid") and not final_state.get("cache_hit"):
        cache_mgr = get_cache_manager()
        profile_summary = {
            "collected_evidence": final_state.get("collected_evidence", {}),
            "cache_type": "collector_cache"
        }
        cache_mgr.write(company_name, domain, profile_summary)
        print("\n> Saved raw collector evidence to cache database.")

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
