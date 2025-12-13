"""Generic code repair agent for unknown/unsupported languages."""

from .base_agent import BaseAgent


class GenericAgent(BaseAgent):
    """
    Generic fallback agent for languages without specialized knowledge.

    Uses minimal prompt focused on basic syntax repair.
    """

    def __init__(self, model, tokenizer):
        # Initialize with generic language (no JSON file needed)
        super().__init__(model, tokenizer, language="generic")

    def _load_knowledge(self) -> dict:
        """
        Override to provide generic repair prompt.

        Returns:
            dict: Minimal generic repair prompt
        """
        return {
            "repair_prompt": "Fix syntax errors in this code. Preserve the original logic and variable names. Output only valid code with no explanations.\n\nCode:\n{code}\n\nFixed code:"
        }
