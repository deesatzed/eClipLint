"""Python code repair specialist."""

from .base_agent import BaseAgent


class PythonAgent(BaseAgent):
    """
    Python-specific code repair agent.

    Loads knowledge from knowledge/python.json including:
    - PEP 8 style guidelines
    - Common IndentationError, SyntaxError, NameError patterns
    - Best practices for modern Python 3.10+
    """

    def __init__(self, model, tokenizer):
        super().__init__(model, tokenizer, language="python")
