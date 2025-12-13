"""Manager agent for routing to language-specific specialists."""

from __future__ import annotations
import sys
from typing import Optional

from .base_agent import BaseAgent
from .python_agent import PythonAgent
from .javascript_agent import JavaScriptAgent
from .bash_agent import BashAgent
from .sql_agent import SQLAgent
from .rust_agent import RustAgent
from .generic_agent import GenericAgent


class ManagerAgent:
    """
    Routes code repair requests to language-specific specialist agents.

    Uses lazy loading: agents are only instantiated when first needed.
    All agents share the same LLM model instance (no redundant loading).
    """

    def __init__(self, model, tokenizer):
        """
        Initialize manager with shared LLM model.

        Args:
            model: mlx-lm model instance (shared across all agents)
            tokenizer: mlx-lm tokenizer instance (shared across all agents)
        """
        self.model = model
        self.tokenizer = tokenizer
        self.agents: dict[str, BaseAgent] = {}  # Lazy-loaded specialist agents

    def route(self, code: str, detected_language: str) -> BaseAgent:
        """
        Route to appropriate specialist agent based on language.

        Agents are lazy-loaded (only instantiated when first needed).

        Args:
            code: Code to repair (not used for routing, but available)
            detected_language: Language detected by heuristic or LLM classifier

        Returns:
            BaseAgent: Specialist agent for this language
        """
        # Normalize language names
        lang = detected_language.lower().strip()

        # Map language to agent class
        agent_map = {
            "python": PythonAgent,
            "javascript": JavaScriptAgent,
            "js": JavaScriptAgent,
            "typescript": JavaScriptAgent,  # Reuse JS agent (similar syntax)
            "ts": JavaScriptAgent,
            "bash": BashAgent,
            "sh": BashAgent,
            "shell": BashAgent,
            "sql": SQLAgent,
            "postgres": SQLAgent,
            "postgresql": SQLAgent,
            "mysql": SQLAgent,
            "rust": RustAgent,
            "rs": RustAgent,
        }

        # Get agent class (default to generic)
        agent_class = agent_map.get(lang, GenericAgent)

        # Use normalized name as cache key (e.g., "javascript" for both "js" and "javascript")
        if lang in ("js", "typescript", "ts"):
            cache_key = "javascript"
        elif lang in ("sh", "shell"):
            cache_key = "bash"
        elif lang in ("postgres", "postgresql", "mysql"):
            cache_key = "sql"
        elif lang in ("rs",):
            cache_key = "rust"
        else:
            cache_key = lang

        # Lazy load agent (instantiate only if not cached)
        if cache_key not in self.agents:
            if self.model is not None:
                # Only print if we're actually loading (not on first check)
                print(f"⚙ Loading {cache_key} specialist agent...", file=sys.stderr, end="", flush=True)

            self.agents[cache_key] = agent_class(self.model, self.tokenizer)

            if self.model is not None:
                print(" ✓", file=sys.stderr)

        return self.agents[cache_key]

    def repair(self, code: str, language: str) -> str:
        """
        Route to appropriate agent and repair code.

        Args:
            code: Broken code to repair
            language: Detected language

        Returns:
            str: Repaired code
        """
        agent = self.route(code, language)
        return agent.repair(code)

    def get_loaded_agents(self) -> list[str]:
        """
        Get list of currently loaded agents (for debugging/stats).

        Returns:
            list[str]: Language names of loaded agents
        """
        return list(self.agents.keys())
