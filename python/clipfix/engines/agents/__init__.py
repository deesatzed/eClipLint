"""
Multi-agent code repair system.

Each language has a specialist agent with dedicated knowledge and prompts.
"""

from .manager import ManagerAgent
from .base_agent import BaseAgent

__all__ = ["ManagerAgent", "BaseAgent"]
