import json
import os

def generate_underwriting_audit_report(final_state, company_name, domain, rule_id):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Underwriting Audit Report - {company_name}</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; color: #333; margin: 0; padding: 20px; }}
            .container {{ max-width: 1200px; margin: auto; background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            h2 {{ color: #2980b9; margin-top: 30px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
            h3 {{ color: #34495e; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th, td {{ padding: 12px; border: 1px solid #ddd; text-align: left; }}
            th {{ background-color: #f8f9fa; font-weight: bold; color: #2c3e50; }}
            tr:nth-child(even) {{ background-color: #fdfdfd; }}
            .badge {{ display: inline-block; padding: 5px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; color: #fff; }}
            .badge.success {{ background-color: #27ae60; }}
            .badge.warning {{ background-color: #f39c12; }}
            .badge.danger {{ background-color: #e74c3c; }}
            .badge.info {{ background-color: #3498db; }}
            .collapsible {{ background-color: #ecf0f1; color: #333; cursor: pointer; padding: 10px; width: 100%; border: none; text-align: left; outline: none; font-size: 16px; border-radius: 4px; margin-top: 10px; font-weight: bold; }}
            .active, .collapsible:hover {{ background-color: #d0d3d4; }}
            .content {{ padding: 0 15px; display: none; overflow: hidden; background-color: #fafafa; border: 1px solid #eee; border-top: none; margin-bottom: 10px; }}
            pre {{ background: #2d2d2d; color: #ccc; padding: 15px; border-radius: 4px; overflow-x: auto; font-family: 'Courier New', Courier, monospace; font-size: 13px; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
            .card {{ background: #fdfdfd; border: 1px solid #e1e1e1; padding: 20px; border-radius: 6px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Underwriting Audit & Debug Report</h1>
            
            <!-- SECTION 1: Executive Underwriting Summary -->
            <h2>1. Executive Underwriting Summary</h2>
            <div class="grid">
                <div class="card">
                    <h3>Target Details</h3>
                    <p><strong>Target Entity:</strong> {company_name}</p>
                    <p><strong>Primary Domain:</strong> {domain}</p>
                    <p><strong>Rule Executed:</strong> {rule_id}</p>
                    <p><strong>Entity Status:</strong> {final_state.get('entity_status', 'Unknown')}</p>
                </div>
                <div class="card">
                    <h3>Verdict Summary</h3>
                    <p><strong>Risk Category:</strong> <span class="badge {'success' if final_state.get('risk_category') == 'Very Favourable' else 'info'}">{final_state.get('risk_category', 'Unknown')}</span></p>
                    <p><strong>Confidence Score:</strong> {final_state.get('confidence_score', 0.0)}%</p>
                    <p><strong>Confidence Band:</strong> {final_state.get('confidence_band', 'Unknown')}</p>
                    <p><strong>Human Escalation:</strong> <span class="badge {'danger' if final_state.get('human_escalation_flag') else 'success'}">{'REQUIRED' if final_state.get('human_escalation_flag') else 'NOT REQUIRED'}</span></p>
                </div>
            </div>
            
            <!-- SECTION 2: Collector Research Trail -->
            <h2>2. Collector Research Trail - Raw JSON Evidence</h2>
    """

    evidence = final_state.get('collected_evidence', {})
    for source_name, data in evidence.items():
        status = data.get('status', 'unknown')
        badge_class = 'success' if status == 'success' else 'danger'
        raw_json = json.dumps(data, indent=2)
        
        html_content += f"""
            <button class="collapsible">{source_name} <span class="badge {badge_class}">{status.upper()}</span></button>
            <div class="content">
                <p><strong>Source Name:</strong> {source_name}</p>
                <p><strong>Status:</strong> {status}</p>
                <h4>Extracted Findings & Raw JSON:</h4>
                <pre>{raw_json}</pre>
            </div>
        """

    priority_order = ["SECCollector", "DBCollector", "Wikidata", "Wikipedia", "DomainScraper"]
    
    # Calculate collector contributions
    collector_contributions = {s: 0 for s in priority_order}
    collector_findings = {s: len(evidence.get(s, {}).get("findings", {})) for s in priority_order}

    # Find winning sources
    reconciled = final_state.get('reconciled_profile', {})
    reconciled_rows = ""
    for k, v in reconciled.items():
        winning_source = "Coordinator Agent (Fallback/Computed)"
        decision = "Defaulted/Computed by LLM"
        
        for source in priority_order:
            findings = evidence.get(source, {}).get("findings", {})
            if k in findings and findings[k] == v:
                winning_source = source
                decision = f"Selected because {source} has highest priority"
                collector_contributions[source] += 1
                break
                
        reconciled_rows += f"<tr><td>{k}</td><td>{v}</td><td><span class='badge info'>{winning_source}</span></td><td>{decision}</td></tr>"

    html_content += f"""
            <!-- SECTION 3: Coordinator Reconciliation & Conflict Decision -->
            <h2>3. Coordinator Reconciliation & Conflict Decision</h2>
            
            <div class="card" style="margin-bottom: 20px;">
                <h3>Collector Contribution Summary</h3>
                <table>
                    <tr><th>Collector</th><th>Fields Contributed</th><th>Successful Findings Count</th></tr>
    """
    for source in priority_order:
        won = collector_contributions[source]
        total = collector_findings[source]
        html_content += f"<tr><td><strong>{source}</strong></td><td>{won}</td><td>{total}</td></tr>"

    html_content += """
                </table>
            </div>
            
            <div class="card">
                <h3>Reconciled Company Profile</h3>
                <div style="overflow-x: auto;">
                <table>
                    <tr><th>Field</th><th>Reconciled Value</th><th>Source Used</th><th>Conflict Decision</th></tr>
    """
    html_content += reconciled_rows
    html_content += """
                </table>
                </div>
                
                <h3>Conflict Decisions</h3>
                <p>Priority rule used: SEC > D&B/GLEIF > Wikidata > Wikipedia > Domain</p>
                <ul>
    """
    conflicts = final_state.get('conflict_flags', [])
    if conflicts:
        for c in conflicts:
            html_content += f"<li><strong>{c.get('parameter')}</strong>: {c.get('details')}</li>"
    else:
        html_content += "<li>No conflicts detected.</li>"
    
    html_content += """
                </ul>
            </div>
            
            <!-- SECTION 4: Step-by-Step Modifier Evaluation Table -->
            <h2>4. Step-by-Step Modifier Evaluation Table</h2>
            <div style="overflow-x: auto;">
            <table>
                <tr>
                    <th>#</th>
                    <th>Modifier Name</th>
                    <th>Reconciled Inputs</th>
                    <th>Excel Rule Reference</th>
                    <th>Math/Code Logic</th>
                    <th>Rating</th>
                </tr>
    """
    
    modifier_meta = {
        "Mergers and Acquisitions": {
            "inputs": lambda r: f"Acquisitions: {len(r.get('acquisitions', []))}",
            "rule": "Points sum compared against revenue-tier thresholds."
        },
        "Amount of sensitive information": {
            "inputs": lambda r: f"Customer: {r.get('customer_type')}, E-com: {r.get('has_ecommerce')}",
            "rule": "B2B, no e-commerce maps to Favourable."
        },
        "Domain Encryption": {
            "inputs": lambda r: f"Total: {len(r.get('domains', []))}, Encrypted: {sum(1 for d in r.get('domains', []) if d.get('https_encrypted'))}",
            "rule": "All domains encrypted maps to Favourable."
        },
        "Geographic Spread": {
            "inputs": lambda r: f"Countries: {len(r.get('countries_of_operation', []))}, Continents: {len(r.get('continent_spread', []))}",
            "rule": "Operations in <= 3 countries on 1 continent = Favourable."
        },
        "Internet footprint": {
            "inputs": lambda r: f"Domains: {r.get('internet_exposure_domains', 0)}, Scale: {r.get('customer_base_scale', '')}",
            "rule": "Domains count * Scale Multiplier (SMB=1, Mid-Market=2, Enterprise=3)."
        },
        "Nature of services": {
            "inputs": lambda r: f"Appetite: {r.get('services_appetite', '')}, SIC: {len(r.get('sic_codes', []))}",
            "rule": "Weighted mapping to low/medium/high risk or SIC fallback."
        },
        "Organizational Complexity": {
            "inputs": lambda r: f"Subsidiaries: {r.get('subsidiaries_count', len(r.get('subsidiaries', [])))}, Revenue: {r.get('revenue', 0)}",
            "rule": "Subsidiary count vs revenue tier."
        },
        "Privacy Regulation": {
            "inputs": lambda r: f"Privacy Policy: {r.get('privacy_policy_published')}, Frameworks: {len(r.get('compliance_mentions', []))}",
            "rule": "Policy published + Compliance frameworks count."
        },
        "Seasonality of sales": {
            "inputs": lambda r: f"Quarterly Revenue: {len(r.get('quarterly_revenue', []))}, SIC: {len(r.get('sic_codes', []))}",
            "rule": "CV of quarterly revenue (CV < 0.1 Favourable, > 0.25 Unfavourable) or SIC benchmark."
        },
        "Volatility/Recovery in Sales": {
            "inputs": lambda r: f"Digital Exposure: {r.get('digital_exposure')}, Disruption Speed: {r.get('disruption_speed')}, Recovery Complexity: {r.get('recovery_complexity')}",
            "rule": "Avg of digital exposure, disruption speed, recovery complexity."
        },
        "Applicability of Privacy Regulation": {
            "inputs": lambda r: f"Countries: {len(r.get('countries_of_operation', []))}, E-com: {r.get('has_ecommerce')}",
            "rule": "Operates in strict regions (GDPR, CCPA) or has e-commerce."
        },
        "B2C End Products": {
            "inputs": lambda r: f"Customer Type: {r.get('customer_type')}",
            "rule": "B2C = average risk, B2B = favourable."
        },
        "Years in business": {
            "inputs": lambda r: f"Founding Year: {r.get('founding_year')}, Revenue: {r.get('revenue', 0)}",
            "rule": "Founding year vs current year compared against revenue-tier thresholds."
        }
    }
    
    modifier_scores = final_state.get('modifier_scores', {})
    rationale = final_state.get('underwriting_rationale', {})
    reconciled = final_state.get('reconciled_profile', {})
    
    idx = 1
    for mod_name, scores in modifier_scores.items():
        score = scores.get('score', '')
        rating = scores.get('rating', '')
        rat_text = rationale.get(mod_name, '')
        
        if mod_name == "Nature of services" and "|" in rat_text:
            parts = [p.strip() for p in rat_text.split('|')]
            formatted_parts = [f"<li>{p}</li>" for p in parts]
            rat_text = f"<ul style='margin:0; padding-left:20px;'>{''.join(formatted_parts)}</ul>"
        
        meta = modifier_meta.get(mod_name, {})
        inputs_str = meta.get("inputs", lambda r: "N/A")(reconciled) if "inputs" in meta else "N/A"
        rule_str = meta.get("rule", "Dynamic evaluation")
        
        rating_display = f"{rating.title()}"
        if score != "" and score != rating:
            rating_display += f" (Score: {score})"
            
        html_content += f"""
                <tr>
                    <td>{idx}</td>
                    <td><strong>{mod_name}</strong></td>
                    <td>{inputs_str}</td>
                    <td>{rule_str}</td>
                    <td>{rat_text}</td>
                    <td><span class="badge info">{rating_display}</span></td>
                </tr>
        """
        idx += 1
        
    html_content += """
            </table>
            </div>
            
            <!-- SECTION 5: Final Verdict Calculations -->
            <h2>5. Final Verdict Calculations</h2>
            <div class="card">
                <h3>Rating-to-Score Mapping</h3>
                <ul>
                    <li>Very Favourable = 1.0</li>
                    <li>Favourable = 2.0</li>
                    <li>Partially Favourable = 3.0</li>
                    <li>Average = 4.0</li>
                    <li>Partially Unfavourable = 5.0</li>
                    <li>Unfavourable = 6.0</li>
                </ul>
    """
    
    # Calculate sum and avg
    rating_map = {
        "very favourable": 1.0,
        "favourable": 2.0,
        "partially favourable": 3.0,
        "average": 4.0,
        "partially unfavourable": 5.0,
        "unfavourable": 6.0
    }
    
    sum_score = 0.0
    count = len(modifier_scores)
    for scores in modifier_scores.values():
        rat = scores.get('rating', '').lower()
        sum_score += rating_map.get(rat, 4.0)
        
    avg_score = sum_score / count if count > 0 else 4.0
    
    html_content += f"""
                <h3>Calculation Details</h3>
                <p><strong>Sum of Modifier Scores:</strong> {sum_score:.2f}</p>
                <p><strong>Average Score Calculation:</strong> {sum_score:.2f} / {count} = {avg_score:.3f}</p>
                <p><strong>Final Risk Category Range:</strong> {final_state.get('risk_category', 'Unknown')}</p>
                <p><strong>Evidence Confidence Score:</strong> {final_state.get('confidence_score', 0.0)}%</p>
                <p><strong>Human Escalation Reason:</strong> {'Score below 50%, conflicts, or mismatch' if final_state.get('human_escalation_flag') else 'None'}</p>
            </div>
            
        </div>
        
        <script>
            var coll = document.getElementsByClassName("collapsible");
            var i;

            for (i = 0; i < coll.length; i++) {{
              coll[i].addEventListener("click", function() {{
                this.classList.toggle("active");
                var content = this.nextElementSibling;
                if (content.style.display === "block") {{
                  content.style.display = "none";
                }} else {{
                  content.style.display = "block";
                }}
              }});
            }}
        </script>
    </body>
    </html>
    """
    
    file_path = "underwriting_audit_report.html"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
