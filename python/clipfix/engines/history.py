from __future__ import annotations
import json, time
from pathlib import Path
import pyperclip

HIST_PATH = Path.home() / ".clipfix_history.jsonl"

def push_history(previous_clipboard: str, max_depth: int = 25) -> None:
    HIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {"ts": time.time(), "text": previous_clipboard}
    with HIST_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    lines = HIST_PATH.read_text(encoding="utf-8").splitlines()
    if len(lines) > max_depth:
        HIST_PATH.write_text("\n".join(lines[-max_depth:]) + "\n", encoding="utf-8")

def undo_history() -> tuple[bool, str]:
    if not HIST_PATH.exists():
        return False, "ecliplint: no history to undo"
    lines = HIST_PATH.read_text(encoding="utf-8").splitlines()
    if not lines:
        return False, "ecliplint: no history to undo"
    last = json.loads(lines[-1])
    pyperclip.copy(last["text"])
    remaining = lines[:-1]
    HIST_PATH.write_text(("\n".join(remaining) + "\n") if remaining else "", encoding="utf-8")
    return True, "ecliplint: undo restored previous clipboard"
