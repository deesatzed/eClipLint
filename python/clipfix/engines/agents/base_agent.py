"""Base agent class for language-specific code repair."""

from __future__ import annotations
from abc import ABC
import json
import sys
from pathlib import Path
from typing import Optional


class BaseAgent(ABC):
    """
    Abstract base class for language-specific repair agents.

    Each agent loads knowledge from a JSON file and uses specialized
    prompts for higher-quality repairs.
    """

    def __init__(self, model, tokenizer, language: str):
        """
        Initialize agent with language-specific knowledge.

        Args:
            model: mlx-lm model instance
            tokenizer: mlx-lm tokenizer instance
            language: Language identifier (matches JSON filename)
        """
        self.model = model
        self.tokenizer = tokenizer
        self.language = language
        self.knowledge = self._load_knowledge()

    def _load_knowledge(self) -> dict:
        """
        Load language-specific knowledge from JSON file.

        Returns:
            dict: Knowledge including repair_prompt, common_errors, style_rules, etc.
                  Falls back to minimal prompt if file missing or invalid.
        """
        # Find knowledge file (handle both installed and development paths)
        knowledge_paths = [
            Path(__file__).parent.parent.parent.parent.parent / "knowledge" / f"{self.language}.json",
            Path(__file__).parent.parent.parent / "knowledge" / f"{self.language}.json",
            Path.cwd() / "knowledge" / f"{self.language}.json",
        ]

        knowledge_path = None
        for path in knowledge_paths:
            if path.exists():
                knowledge_path = path
                break

        if not knowledge_path:
            print(
                f"⚠ Warning: Knowledge file for {self.language} not found. Using generic prompt.",
                file=sys.stderr
            )
            return {
                "repair_prompt": f"Fix syntax errors in this {self.language} code. Output only valid code, no explanations.\n\nCode:\n{{code}}\n\nFixed code:"
            }

        try:
            with open(knowledge_path, encoding="utf-8") as f:
                knowledge = json.load(f)
                return knowledge
        except json.JSONDecodeError as e:
            print(
                f"⚠ Warning: Invalid JSON in {knowledge_path}: {e}. Using generic prompt.",
                file=sys.stderr
            )
            return {
                "repair_prompt": f"Fix syntax errors in this {self.language} code. Output only valid code.\n\nCode:\n{{code}}\n\nFixed code:"
            }
        except Exception as e:
            print(
                f"⚠ Warning: Error loading {knowledge_path}: {e}. Using generic prompt.",
                file=sys.stderr
            )
            return {
                "repair_prompt": f"Fix syntax errors in this {self.language} code.\n\nCode:\n{{code}}\n\nFixed code:"
            }

    def repair(self, code: str) -> str:
        """
        Repair code using language-specific knowledge and LLM.

        Args:
            code: Broken code to repair

        Returns:
            str: Repaired code (fences stripped, newline added)
        """
        # Get prompt template from knowledge
        prompt_template = self.knowledge.get(
            "repair_prompt",
            f"Fix syntax errors in this {self.language} code:\n{{code}}\n\nFixed code:"
        )

        # Format prompt with actual code
        prompt = prompt_template.format(code=code)

        # Apply chat template if available
        if self.tokenizer.chat_template:
            prompt = self.tokenizer.apply_chat_template(
                [{"role": "user", "content": prompt}],
                add_generation_prompt=True
            )

        # Generate repair
        from mlx_lm import generate

        # Get max_tokens from knowledge or use default
        max_tokens = self.knowledge.get("max_tokens", 2048)

        raw = generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
            verbose=False  # Keep quiet (progress handled elsewhere)
        )

        # Strip markdown fences and return
        return self._strip_fences(raw)

    @staticmethod
    def _strip_fences(text: str) -> str:
        """
        Remove markdown code fences from LLM output.

        LLMs often wrap code in ```language ... ``` fences.
        This removes them to get clean code.

        Args:
            text: Raw LLM output

        Returns:
            str: Code without fences, with trailing newline
        """
        lines = text.strip().splitlines()

        # Remove opening fence (```python, ```javascript, etc.)
        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        # Remove closing fence (```)
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]

        return "\n".join(lines).strip() + "\n"

    def get_style_rules(self) -> list[str]:
        """
        Get style rules for this language.

        Returns:
            list[str]: Style rules from knowledge, or empty list
        """
        return self.knowledge.get("style_rules", [])

    def get_common_errors(self) -> list[dict]:
        """
        Get common errors for this language.

        Returns:
            list[dict]: Common errors from knowledge, or empty list
        """
        return self.knowledge.get("common_errors", [])
