"""SQL query repair specialist."""

from .base_agent import BaseAgent


class SQLAgent(BaseAgent):
    """
    SQL query repair agent (PostgreSQL dialect).

    Loads knowledge from knowledge/sql.json including:
    - SQL syntax rules
    - JOIN best practices
    - Keyword capitalization conventions
    - Common syntax errors
    """

    def __init__(self, model, tokenizer):
        super().__init__(model, tokenizer, language="sql")
