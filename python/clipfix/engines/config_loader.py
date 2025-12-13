from __future__ import annotations
from pathlib import Path
import os
import yaml

_CFG = None

def find_repo_root(start: Path) -> Path | None:
    for p in start.resolve().parents:
        if (p / "config" / "llm.yaml").exists():
            return p
    return None

def load_llm_config() -> dict:
    global _CFG
    if _CFG is not None:
        return _CFG

    override = os.environ.get("CLIPFIX_CONFIG")
    if override:
        cfg_path = Path(override).expanduser().resolve()
    else:
        here = Path(__file__).resolve()
        root = find_repo_root(here)
        if root is None:
            raise FileNotFoundError("clipfix: could not locate config/llm.yaml (set CLIPFIX_CONFIG)")
        cfg_path = root / "config" / "llm.yaml"

    with cfg_path.open() as f:
        _CFG = yaml.safe_load(f)
    return _CFG
