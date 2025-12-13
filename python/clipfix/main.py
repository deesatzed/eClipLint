from __future__ import annotations
import argparse
import difflib
import os
import sys
import pyperclip

from clipfix.engines.history import push_history, undo_history
from clipfix.engines.detect_and_format import process_text


def print_diff(before: str, after: str):
    """
    Print unified diff with color.

    Args:
        before: Original code
        after: Formatted code
    """
    diff = difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile="before",
        tofile="after",
        lineterm=""
    )

    # Color output if terminal supports it (check TERM env var)
    use_color = os.environ.get("TERM", "").lower() not in ("", "dumb")

    for line in diff:
        if use_color:
            if line.startswith('+') and not line.startswith('+++'):
                print(f"\033[32m{line}\033[0m", end="")  # Green
            elif line.startswith('-') and not line.startswith('---'):
                print(f"\033[31m{line}\033[0m", end="")  # Red
            elif line.startswith('@@'):
                print(f"\033[36m{line}\033[0m", end="")  # Cyan
            else:
                print(line, end="")
        else:
            print(line, end="")


def print_success(before: str, after: str, mode: str):
    """
    Print success message with change summary.

    Args:
        before: Original code
        after: Formatted code
        mode: Processing mode (formatted, repaired+formatted, etc.)
    """
    if before == after:
        print("✓ ecliplint: no changes needed")
        return

    # Count lines changed
    before_lines = before.splitlines()
    after_lines = after.splitlines()

    lines_changed = sum(
        1 for b, a in zip(before_lines, after_lines) if b != a
    )
    lines_added = len(after_lines) - len(before_lines)

    # Build summary
    summary_parts = [f"{lines_changed} lines modified"]

    if lines_added > 0:
        summary_parts.append(f"{lines_added} lines added")
    elif lines_added < 0:
        summary_parts.append(f"{-lines_added} lines removed")

    summary = ", ".join(summary_parts)
    print(f"✓ ecliplint: {mode} ({summary})")


def main(argv=None):
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

    ap = argparse.ArgumentParser(
        prog="ecliplint",
        description="Clipboard code formatter with LLM-powered repair"
    )
    ap.add_argument("--undo", action="store_true", help="Restore previous clipboard")
    ap.add_argument("--no-llm", action="store_true", help="Disable LLM fallback")
    ap.add_argument("--diff", action="store_true", help="Show changes without modifying clipboard")
    ap.add_argument("--max-history", type=int, default=25, help="Maximum undo history depth")
    args = ap.parse_args(argv)

    if args.undo:
        ok, msg = undo_history()
        print(("✔ " if ok else "✖ ") + msg, file=sys.stderr if not ok else sys.stdout)
        return 0 if ok else 2

    raw = pyperclip.paste()
    if not raw or not raw.strip():
        print("✖ ecliplint: clipboard empty", file=sys.stderr)
        return 1

    ok, out, mode = process_text(raw, allow_llm=(not args.no_llm))
    if not ok:
        print(f"✖ ecliplint failed: {mode}", file=sys.stderr)
        return 2

    # Diff mode: show changes without modifying clipboard
    if args.diff:
        if out == raw:
            print("✓ No changes needed")
        else:
            print_diff(raw, out)
        return 0

    # Apply mode: modify clipboard and show summary
    if out != raw:
        push_history(raw, max_depth=args.max_history)
        pyperclip.copy(out)

    print_success(raw, out, mode)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
