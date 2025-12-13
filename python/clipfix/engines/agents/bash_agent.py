"""Bash/shell script repair specialist."""

from .base_agent import BaseAgent


class BashAgent(BaseAgent):
    """
    Bash/shell script repair agent.

    Loads knowledge from knowledge/bash.json including:
    - Shellcheck-recommended best practices
    - Variable quoting rules
    - Conditional syntax requirements
    - Common missing keyword errors
    """

    def __init__(self, model, tokenizer):
        super().__init__(model, tokenizer, language="bash")
