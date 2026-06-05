# Cyber Risk Predictor (Underwriting Rating Modifier)

A Python-based agentic underwriting tool built using **LangGraph**. It automates gathering company information from multiple sources, fact-checking it, and evaluating it against **10 underwriting risk modifiers** driven directly by a master Excel rule sheet.

---

## 🚀 Key Features

* **LangGraph Multi-Agent Architecture:** Handles validation, coordination, fact-checking, and underwriting in structured graph nodes.
* **3-Tier Cache System:** Speeds up evaluation and reduces API calls by checking for previous evaluations using Exact, Fuzzy, and Domain matches.
* **Excel-Driven Rules:** Loads underwriting modifier rules directly from `data/cyber_rater_modifier_summary.xlsx`.
* **Parallel Collectors:** Simulates gathering data from 6 sources concurrently (Web Search, SEC filings, D&B registry, etc.) to minimize processing time.
* **Accuracy Guardrails:** Fact-checks findings across sources and flags entities for human escalation if consistency/confidence is low.

---

## 📁 Project Structure

```
CyberRiskInsurance/
├── config/
│   └── config.json             # App configuration settings (cache path, etc.)
├── data/
│   ├── cyber_rater_modifier_summary.xlsx  # Underwriter modifier Excel sheet
│   ├── cache/
│   │   └── company_cache.json  # Local JSON cache database (ignored by Git)
│   └── mock_sources/
│       └── mock_companies.json # Mock search data for local demo run
├── src/
│   ├── main.py                 # CLI entrypoint to evaluate a company
│   ├── state.py                # LangGraph state definition
│   ├── graph.py                # LangGraph workflow setup and wiring
│   ├── supervisor.py           # Supervisor node (input validation & caching)
│   ├── coordinator.py          # Coordinator node (data reconciliation)
│   ├── fact_checker.py         # Fact Checker node (corroborating facts)
│   └── underwriter.py          # Underwriter node (calculates modifier ratings)
├── tests/
│   ├── test_modifiers.py       # Unit tests for the 10 Excel modifiers
│   └── test_workflow.py        # Integration tests for the LangGraph flow
├── requirements.txt            # Python dependencies
└── README.md                   # This project guide
```

---

## 🛠️ Setup & Installation

1. **Navigate to the project directory:**
   ```bash
   cd /Users/shimodi/Documents/AgenticProjects/CyberRiskInsurance
   ```

2. **(Optional) Create a Python virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

---

## 💻 How to Use

To evaluate a company and see its risk rating, run `src/main.py` using CLI options:

```bash
# Run the evaluation CLI
PYTHONPATH=. python3 src/main.py --name "TechGiant Inc." --domain "techgiant.com"
```

### Options:
* `--name` or `-n`: The company name (e.g. "TechGiant Inc.")
* `--domain` or `-d`: The primary domain name (e.g. "techgiant.com")

---

## 🧪 Running Unit Tests

To run the automated test suite verifying both the 10 underwriting modifiers and the LangGraph workflow structure:

```bash
python3 -m unittest discover -s tests
```
