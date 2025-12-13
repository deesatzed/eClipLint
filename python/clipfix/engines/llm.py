from __future__ import annotations
import json
import sys
from pathlib import Path
from mlx_lm import load, generate

from .config_loader import load_llm_config
from .agents.manager import ManagerAgent

_MODEL = None
_TOKENIZER = None
_MANAGER = None  # Agent manager (lazy-loaded)

def _strip_fences(text: str) -> str:
    lines = text.strip().splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()

def _load_model():
    """Load LLM model with progress feedback."""
    global _MODEL, _TOKENIZER
    if _MODEL is not None:
        return _MODEL, _TOKENIZER

    cfg = load_llm_config()["llm"]
    active = cfg["model"]["active"]
    model_cfg = cfg["model"]["options"][active]

    # Check if model is cached (avoid long wait message if already downloaded)
    cache_dir = Path.home() / ".cache/huggingface/hub"
    model_name = model_cfg["repo"].split("/")[1]
    model_cached = cache_dir.exists() and any(model_name in str(p) for p in cache_dir.glob("*"))

    if not model_cached:
        print(
            f"⚠ First-time setup: Downloading {model_cfg['repo']} (~4GB)...",
            file=sys.stderr
        )
        print(
            "  This will take 1-5 minutes. Subsequent runs will be fast.",
            file=sys.stderr
        )
    else:
        print("⏳ Loading model...", file=sys.stderr, end="", flush=True)

    _MODEL, _TOKENIZER = load(model_cfg["repo"])

    if model_cached:
        print(" ✓", file=sys.stderr)

    return _MODEL, _TOKENIZER

def _get_manager() -> ManagerAgent:
    """Get or create agent manager (lazy-loaded)."""
    global _MANAGER
    if _MANAGER is not None:
        return _MANAGER

    model, tokenizer = _load_model()
    _MANAGER = ManagerAgent(model, tokenizer)
    return _MANAGER

def llm_classify(text: str) -> dict:
    """Classify code language using LLM (with progress feedback)."""
    cfg = load_llm_config()["llm"]
    if not cfg.get("enabled", True):
        return {"kind": "unknown", "inner_kind": None}

    print("🔍 Classifying code...", file=sys.stderr, end="", flush=True)

    model, tokenizer = _load_model()
    prompt_t = cfg["prompts"]["classify"]
    prompt = prompt_t.format(text=text[:8000])

    if tokenizer.chat_template is not None:
        prompt = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            add_generation_prompt=True,
        )

    raw = generate(
        model,
        tokenizer,
        prompt=prompt,
        max_tokens=512,
        verbose=cfg["generation"].get("verbose", False),
    )

    print(" ✓", file=sys.stderr)

    cleaned = _strip_fences(raw)
    # Try to locate first JSON object
    start = cleaned.find("{")
    if start == -1:
        return {"kind": "unknown", "inner_kind": None}
    cleaned = cleaned[start:]
    end = cleaned.rfind("}")
    if end != -1:
        cleaned = cleaned[: end + 1]
    try:
        obj = json.loads(cleaned)
        return {"kind": obj.get("kind", "unknown"), "inner_kind": obj.get("inner_kind")}
    except Exception:
        return {"kind": "unknown", "inner_kind": None}

def llm_repair(language: str, code: str) -> str:
    """
    Repair code using multi-agent system (with progress feedback).

    Routes to language-specific specialist agent for higher quality repairs.
    """
    cfg = load_llm_config()["llm"]
    if not cfg.get("enabled", True):
        raise RuntimeError("LLM disabled")

    print(f"🔧 Repairing {language} code...", file=sys.stderr, end="", flush=True)

    # Use agent manager for language-specific repair
    manager = _get_manager()
    repaired = manager.repair(code, language)

    print(" ✓", file=sys.stderr)

    return repaired
