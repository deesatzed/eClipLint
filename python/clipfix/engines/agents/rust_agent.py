"""Rust code repair specialist."""

from .base_agent import BaseAgent


class RustAgent(BaseAgent):
    """
    Rust code repair agent.

    Loads knowledge from knowledge/rust.json including:
    - Rust naming conventions (snake_case, PascalCase)
    - Common syntax errors (missing semicolons, wrong match syntax)
    - Idiomatic Rust patterns
    - Rustfmt style guidelines
    """

    def __init__(self, model, tokenizer):
        super().__init__(model, tokenizer, language="rust")
