import os

# Expose key classes
from src.factory import AgentFactory
from src.registry import BusinessRuleRegistry
from src.cache import get_cache_manager, CachingCollectorWrapper
from src.supervisor import supervisor_node

# Load .env file automatically from project root if it exists
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(env_path):
    try:
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip().strip('"').strip("'")
    except Exception:
        pass
