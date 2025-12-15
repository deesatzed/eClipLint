from __future__ import annotations
import json
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import Tuple

from .segmenter import regex_segment
from .llm import llm_classify, llm_repair
from .cache import cache_get, cache_put

def _has_cmd(cmd: str) -> bool:
    return subprocess.call(["bash","-lc", f"command -v {cmd} >/dev/null 2>&1"]) == 0

def _format_json(s: str) -> str:
    obj = json.loads(s)
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"

def _format_yaml(s: str) -> str:
    try:
        from ruamel.yaml import YAML
        y = YAML()
        y.indent(mapping=2, sequence=4, offset=2)
        data = y.load(s)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "out.yaml"
            with p.open("w", encoding="utf-8") as f:
                y.dump(data, f)
            return p.read_text(encoding="utf-8")
    except Exception:
        return s

def _run_file_formatter(cmd: list[str], content: str, ext: str) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / f"in.{ext}"
        p.write_text(content)
        proc = subprocess.run(cmd + [str(p)], capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError((proc.stderr or proc.stdout).strip())
        return p.read_text()

def _format_code(kind: str, code: str) -> Tuple[str, str]:
    """
    Format code and return (formatted_code, formatter_used).

    Returns:
        Tuple of (formatted_code, formatter_name)
    """
    k = (kind or "").lower()

    if k == "json":
        return _format_json(code), "json.dumps"
    if k == "yaml":
        return _format_yaml(code), "ruamel.yaml"

    if k == "python":
        if _has_cmd("ruff"):
            return _run_file_formatter(["ruff","format"], textwrap.dedent(code), "py"), "ruff"
        if _has_cmd("black"):
            return _run_file_formatter(["black","--quiet"], textwrap.dedent(code), "py"), "black"
        return textwrap.dedent(code).strip() + "\n", "dedent"

    if k == "bash":
        if _has_cmd("shfmt"):
            return _run_file_formatter(["shfmt","-w","-i","2","-ci"], code, "sh"), "shfmt"
        return code, "none"

    if k == "rust":
        if _has_cmd("rustfmt"):
            return _run_file_formatter(["rustfmt"], code, "rs"), "rustfmt"
        return code, "none"

    if k in ("javascript","js"):
        if _has_cmd("prettier"):
            return _run_file_formatter(["prettier","--write","--parser","babel"], code, "js"), "prettier"
        return code, "none"

    if k in ("typescript","ts"):
        if _has_cmd("prettier"):
            return _run_file_formatter(["prettier","--write","--parser","typescript"], code, "ts"), "prettier"
        return code, "none"

    if k == "sql":
        if _has_cmd("sqlfluff"):
            return _run_file_formatter(["sqlfluff","fix","--dialect","postgres"], code, "sql"), "sqlfluff"
        return code, "none"

    return code, "none"

def _detect_kind(text: str) -> str:
    t = text.strip()
    low = t.lower()

    # 1) JSON (try parsing first - most specific)
    try:
        json.loads(t)
        return "json"
    except Exception:
        pass

    # 2) Strong Python signals
    if "import " in low or ("from " in low and " import " in low):
        return "python"

    # 3) JavaScript/TypeScript (check BEFORE general keywords)
    # Strong JS signals: const, let, var, arrow functions
    if any(kw in low for kw in ["const ", "let ", "var ", " => "]):
        return "javascript"
    if "interface " in t or ": string" in t or ": number" in t:
        return "typescript"
    # Weaker signals (after checking const/let/var)
    if "function" in low:
        return "javascript"

    # 4) Bash
    if low.startswith("#!/bin/bash") or "set -e" in low or low.startswith("pythonpath="):
        return "bash"

    # 5) Rust
    if "fn main" in low or "use std::" in low or "impl " in low:
        return "rust"

    # 6) SQL (LAST, weakest heuristic)
    if any(x in low for x in ["select ", " join ", " where "]):
        return "sql"

    # Default
    return "python"

def process_text(text: str, allow_llm: bool, lang_override: str = None) -> tuple[bool, str, str]:
    segs = regex_segment(text)
    out_parts = []
    mode = "formatted"

    for seg in segs:
        # Use language override if provided
        if lang_override:
            kind = lang_override.lower()
        else:
            kind = seg.inner_kind or (seg.kind if seg.kind not in ("raw",) else _detect_kind(seg.text))

        # LLM classify if still ambiguous
        if allow_llm and (kind in ("unknown", "raw", "") or kind not in ("python","bash","rust","javascript","typescript","sql","json","yaml")):
            cls = llm_classify(seg.text)
            kind = cls.get("inner_kind") or cls.get("kind") or kind

        # Check cache first
        cached_result = cache_get(seg.text, kind)
        if cached_result is not None:
            # Cache hit!
            cached_success, cached_output, cached_mode = cached_result
            if cached_success:
                out_parts.append(seg.prefix + cached_output + seg.suffix)
                mode = cached_mode
                continue

        # Cache miss - format normally
        try:
            formatted, formatter_used = _format_code(kind, seg.text)

            # Store in cache if successful
            cache_put(seg.text, kind, formatter_used, True, formatted, "formatted")

        except Exception as e:
            if not allow_llm:
                return False, "", f"format error ({kind}): {e}"
            repaired = llm_repair(kind, seg.text)
            try:
                formatted, formatter_used = _format_code(kind, repaired)
                mode = "repaired+formatted"
                # Don't cache LLM repairs (non-deterministic)
            except Exception as e2:
                return False, "", f"repair+format error ({kind}): {e2}"

        out_parts.append(seg.prefix + formatted + seg.suffix)

    return True, "".join(out_parts), mode
