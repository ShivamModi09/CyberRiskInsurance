import os
import re
import sys
import logging
import contextvars
from datetime import datetime

# Context variables for thread/async-isolated log runs
current_run_id = contextvars.ContextVar("current_run_id", default="")
current_log_date = contextvars.ContextVar("current_log_date", default="")
current_log_time = contextvars.ContextVar("current_log_time", default="")
current_company_name = contextvars.ContextVar("current_company_name", default="")
current_rule_id = contextvars.ContextVar("current_rule_id", default="cyber_risk_rating")

MODIFIER_FOLDER_MAPPING = {
    "mergers and acquisitions": "mergers_and_acquisitions",
    "amount of sensitive information": "sensitive_information",
    "domain encryption": "domain_encryption",
    "geographic spread": "geographic_spread",
    "internet footprint": "internet_footprint",
    "nature of services": "nature_of_services",
    "organizational complexity": "organizational_complexity",
    "privacy regulation": "privacy_regulation",
    "seasonality of sales": "seasonality_of_sales",
    "volatility/recovery in sales": "volatility_recovery_in_sales",
    "volatilityrecovery in sales": "volatility_recovery_in_sales",
    "applicability of privacy regulation": "applicability_privacy_regulation",
    "b2c end products": "b2c_end_products",
    "years in business": "years_in_business"
}

def slugify(text: str) -> str:
    """Converts a text string into a clean lowercase filename-friendly slug."""
    text = text.lower().strip()
    text = text.replace("/", "_")
    text = re.sub(r'[^a-z0-9\s_-]', '', text)
    text = re.sub(r'[\s_]+', '_', text)
    return text

def start_run_logging(rule_id: str, company_name: str) -> str:
    """Initializes the logging context variables for a single execution run."""
    import uuid
    run_id = str(uuid.uuid4())[:8]
    now = datetime.now()
    
    current_run_id.set(run_id)
    current_log_date.set(now.strftime("%Y-%m-%d"))
    current_log_time.set(now.strftime("%H-%M-%S"))
    current_company_name.set(company_name)
    current_rule_id.set(rule_id)
    
    return run_id

def get_agent_logger(agent_name: str) -> logging.Logger:
    """Gets a thread-safe, isolated logger for a specific agent/modifier."""
    run_id = current_run_id.get()
    
    # Fallback to standard console logger if logging is not initialized
    if not run_id:
        logger = logging.getLogger(f"cyber_risk_insurance.default.{agent_name}")
        if not logger.handlers:
            logger.setLevel(logging.INFO)
            sh = logging.StreamHandler(sys.stdout)
            sh.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
            logger.addHandler(sh)
        return logger

    # Isolated logger per run and agent name
    logger_name = f"cyber_risk_insurance.{run_id}.{agent_name}"
    logger = logging.getLogger(logger_name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        # Formatter format matching the manager's screenshots:
        # e.g., 2026-06-12 12:55:43 | INFO | src.collectors | message
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console Stream Handler
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(formatter)
        logger.addHandler(sh)
        
        # File Handler
        log_date = current_log_date.get()
        log_time = current_log_time.get()
        company_name = current_company_name.get()
        
        # Slugify folders
        cleaned_name = agent_name.lower()
        if "collector" in cleaned_name or "scraper" in cleaned_name:
            folder_slug = "collectors"
        elif "coordinator" in cleaned_name:
            folder_slug = "coordinator"
        elif "factchecker" in cleaned_name or "fact_checker" in cleaned_name or "fact checker" in cleaned_name:
            folder_slug = "fact_checker"
        elif "underwriter" in cleaned_name:
            folder_slug = "underwriter"
        else:
            folder_slug = MODIFIER_FOLDER_MAPPING.get(cleaned_name, slugify(agent_name))
            
        company_slug = slugify(company_name)
        
        log_dir = os.path.join("logs", log_date, folder_slug, company_slug)
        try:
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f"run_{log_time}.log")
            
            fh = logging.FileHandler(log_file, encoding='utf-8')
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except Exception as e:
            # Fallback if file logging directory creation fails
            sh.stream.write(f"[WARNING] Failed to configure file logging for {agent_name}: {e}\n")
            
    return logger

