"""JavaScript/TypeScript code repair specialist."""

from .base_agent import BaseAgent


class JavaScriptAgent(BaseAgent):
    """
    JavaScript/TypeScript code repair agent.

    Loads knowledge from knowledge/javascript.json including:
    - ES6+ modern syntax
    - JavaScript Standard Style guidelines
    - Common SyntaxError patterns
    - Const/let best practices
    """

    def __init__(self, model, tokenizer):
        super().__init__(model, tokenizer, language="javascript")
