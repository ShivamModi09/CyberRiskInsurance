import os
import json
import re
from datetime import datetime
from typing import Dict, Any
from langchain_groq import ChatGroq
from src.config import PromptTemplate

class BaseAgent:
    def __init__(self, config: Any, tracker: Any = None):
        self.config = config
        self.tracker = tracker

    def get_logger(self) -> Any:
        from src.utils.logger import get_agent_logger
        agent_name = getattr(self.config, 'name', self.__class__.__name__)
        return get_agent_logger(agent_name)

    def format_prompt(self, template: PromptTemplate, **kwargs) -> str:
        # Framework default variables
        now = datetime.now()
        framework_vars = {
            "current_year": str(now.year),
            "today_str": now.strftime("%Y-%m-%d"),
            "format_instructions": "Your output must be a single, valid JSON block. Do not include markdown ticks (like ```json), explanations, or notes."
        }
        
        # Merge prompt_vars from agent configuration if defined
        config_vars = {}
        if hasattr(self.config, 'prompt_vars') and self.config.prompt_vars:
            config_vars = self.config.prompt_vars
            
        merged = {**framework_vars, **config_vars, **kwargs}
        return template.format(**merged)

    def call_llm(self, prompt: str, temperature: float = 0.0) -> str:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is missing. Live Groq API execution is required in production.")

        logger = self.get_logger()
        agent_name = getattr(self.config, 'name', self.__class__.__name__)
        logger.info(f"[{agent_name}] Invoking LLM for prompt/extraction...")
        logger.info(f"[{agent_name}] Prompt input sent to LLM:\n{prompt}")

        # Initialize the live Groq model
        model_name = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
        llm = ChatGroq(
            model=model_name,
            api_key=api_key,
            temperature=temperature
        )
        
        try:
            res = llm.invoke(prompt)
            prompt_tokens = 0
            completion_tokens = 0
            
            # Track token usage if tracker is present
            if hasattr(res, 'response_metadata') and res.response_metadata:
                token_usage = res.response_metadata.get('token_usage', {})
                if token_usage:
                    prompt_tokens = token_usage.get('prompt_tokens', 0)
                    completion_tokens = token_usage.get('completion_tokens', 0)
                    if self.tracker:
                        self.tracker.add_usage(prompt_tokens, completion_tokens)
            
            # Calculate cost estimate based on $0.59/M input, $0.79/M output
            cost = (prompt_tokens * 0.59 + completion_tokens * 0.79) / 1000000.0
            
            # Log usage & outputs
            logger.info(f"[{agent_name}] LLM Response received. Usage: input={prompt_tokens}, output={completion_tokens}, reasoning=0, cached=0, tool_calls=0, cost=${cost:.6f}")
            logger.info(f"[{agent_name}] Output text:\n{str(res.content)}")
            
            return str(res.content)
        except Exception as e:
            import traceback
            logger.error(f"[{agent_name}] LLM invocation failed: {e}\nTraceback:\n{traceback.format_exc()}")
            raise RuntimeError(f"Error calling live Groq model: {e}")

    def parse_json(self, text: str) -> Dict[str, Any]:
        cleaned = text.strip()
        # Clean any markdown code blocks
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            # Fallback regex to find JSON object structure
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            raise ValueError(f"Failed to parse LLM output as JSON. Output was: {text}. Error: {e}")

class BaseCollectorAgent(BaseAgent):
    pass

class BaseCoordinatorAgent(BaseAgent):
    pass

class BaseFactCheckerAgent(BaseAgent):
    pass

class BaseUnderwriterAgent(BaseAgent):
    pass
