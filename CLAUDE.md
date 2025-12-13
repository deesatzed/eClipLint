# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**clipfix** is a production-ready clipboard code formatter that reads from the clipboard, fixes and formats code, then writes back to the clipboard. It uses deterministic formatters first and falls back to a local LLM (mlx-lm) when formatting fails.

**Key Features**:
- Supports: Python, Bash, Rust, JavaScript, TypeScript, SQL, YAML, JSON
- Handles mixed inputs (bash heredocs containing Python, markdown fenced code blocks)
- LLM fallback for code repair when formatters fail
- History/undo functionality
- Zero network dependency (uses local Apple MLX models)

**Tech Stack**: Python 3.10+, mlx-lm (local LLM), PyOxidizer (binary packaging)

## Common Commands

### Development Workflow

Run clipfix directly without install:
```bash
./run_clipfix.sh              # Process clipboard
./run_clipfix.sh --undo       # Restore previous clipboard
./run_clipfix.sh --no-llm     # Disable LLM fallback
```

Install in editable mode:
```bash
pip install -e python
clipfix                       # Run from anywhere
```

### Testing

Run tests:
```bash
pytest tests/                              # All tests
pytest tests/test_segmenter.py            # Single test file
pytest -v                                  # Verbose output
pytest --cov=clipfix --cov-report=html    # With coverage
```

Startup validation tests (manual):
```bash
# See STARTUP_TESTS.md for copy/paste test cases
./run_clipfix.sh    # Run after copying each test case
```

### Building Binary

Build standalone executable with PyOxidizer:
```bash
pyoxidizer build                    # Build binary
./build/*/release/clipfix           # Run built binary
pyoxidizer run                      # Build and run
```

## Architecture

### Processing Pipeline

The core flow is: **clipboard → segment → classify → format/repair → clipboard**

1. **main.py**: Entry point, clipboard I/O, history management
2. **segmenter.py**: Detects special structures (bash heredocs, markdown fences)
3. **detect_and_format.py**: Orchestrates classification and formatting
4. **llm.py**: LLM-based classification and repair (mlx-lm)
5. **history.py**: Undo functionality via `~/.clipfix_history.jsonl`

### Segmentation Strategy

**Special cases** are detected via regex patterns:

- **Bash Python heredoc**: `python - <<'PY' ... PY` → preserves bash wrapper, formats Python inside
- **Markdown fences**: ` ```python ... ``` ` → preserves fences, formats inner code
- **Raw text**: Everything else → classified heuristically or via LLM

Segments have:
- `kind`: Overall structure type (bash_python_heredoc, markdown_fence, raw)
- `inner_kind`: Language of embedded code (python, javascript, etc.)
- `prefix`/`suffix`: Preserved wrappers

### Formatter Hierarchy

For each language, tries formatters in order of availability:

**Python**: ruff format → black → dedent
**Bash**: shfmt
**Rust**: rustfmt
**JavaScript**: prettier (babel parser)
**TypeScript**: prettier (typescript parser)
**SQL**: sqlfluff (postgres dialect)
**JSON**: stdlib json.dumps with indent
**YAML**: ruamel.yaml

If formatting **fails** and `--no-llm` not set:
1. LLM repairs the code (`llm_repair`)
2. Retry formatter on repaired code
3. Return "repaired+formatted" mode

### LLM Integration

Uses **mlx-lm** (Apple Silicon optimized) for two tasks:

**Classification** (`llm_classify`):
- Input: Ambiguous clipboard text
- Output: JSON with `kind` and `inner_kind`
- Model: Configurable in `config/llm.yaml`

**Repair** (`llm_repair`):
- Input: Code that failed formatting + language hint
- Output: Fixed code (stripped of markdown fences)
- Prompt: "Fix syntax errors, preserve intent, output only valid code"

**Model loading**: Lazy (on first use), cached globally

**Configuration**: `config/llm.yaml`
- Active model: `qwen25coder` (Qwen2.5-Coder-7B-Instruct-4bit)
- Alternate: `ministral` (Ministral-3-8B-Instruct)
- Prompts: Fully customizable

### History Management

**File**: `~/.clipfix_history.jsonl`
**Format**: One JSON entry per line: `{"ts": <unix-time>, "text": "<clipboard>"}`
**Max depth**: 25 entries (configurable via `--max-history`)

**Undo** restores last entry and removes it from history.

## File Structure

```
clipfix_production/
├── python/                      # Python package source
│   ├── clipfix/
│   │   ├── main.py             # Entry point (CLI, clipboard I/O)
│   │   └── engines/
│   │       ├── segmenter.py    # Detect heredocs/fences
│   │       ├── detect_and_format.py  # Formatter orchestration
│   │       ├── llm.py          # mlx-lm classify/repair
│   │       ├── config_loader.py  # Load config/llm.yaml
│   │       └── history.py      # Undo system
│   └── pyproject.toml          # Python package config
├── config/
│   └── llm.yaml                # LLM model and prompt config
├── tests/
│   ├── test_segmenter.py       # Regex segment tests
│   └── test_process_json.py    # JSON formatting tests
├── pyoxidizer.bzl              # PyOxidizer build config
├── Cargo.toml                  # Rust build metadata (for PyOxidizer)
├── run_clipfix.sh              # Quick-run wrapper (no install)
├── README.md                   # User-facing docs
├── STARTUP_TESTS.md            # Manual test cases
└── clipfix                     # Built binary (after pyoxidizer build)
```

## Development Guidelines

### Code Modification Patterns

**Adding a new language**:
1. Add formatter in `_format_code()` (detect_and_format.py:41)
2. Add heuristic in `_detect_kind()` (detect_and_format.py:83)
3. Update LLM prompts in `config/llm.yaml` to include new language
4. Add test case in `tests/`

**Modifying LLM behavior**:
- Edit prompts in `config/llm.yaml` (classify, repair_generic)
- Change active model: Update `llm.model.active` in config
- Add new model: Add entry to `llm.model.options`

**Changing segmentation logic**:
- Edit regex patterns in `segmenter.py` (_MD_FENCE, _PY_HEREDOC)
- Add new segment kind: Update Segment dataclass and process_text loop

### Testing Approach

**Unit tests**: Focus on segmenter logic (regex patterns)
**Integration tests**: JSON formatting (no LLM required)
**Manual tests**: STARTUP_TESTS.md (copy/paste/verify)

Tests should **NOT** require LLM by default (slow, non-deterministic). Use `--no-llm` or mock LLM calls.

### Dependencies

**Core** (always required):
- pyperclip: Clipboard access
- pyyaml: Config loading
- mlx-lm, transformers, tokenizers: Local LLM

**Optional** (improves formatting):
- black or ruff: Python
- shfmt: Bash
- rustfmt: Rust
- prettier: JS/TS
- sqlfluff: SQL
- ruamel.yaml: YAML

Check availability via `_has_cmd()` in detect_and_format.py

## Configuration

### Environment Variables

Set in shell or `.env` (not tracked):
```bash
TOKENIZERS_PARALLELISM=false       # Avoid mlx-lm warnings
HF_HUB_DISABLE_PROGRESS_BARS=1    # Suppress download progress
```

These are set automatically by `main.py` and `run_clipfix.sh`.

### LLM Configuration

Edit `config/llm.yaml`:

**Switch models**:
```yaml
llm:
  model:
    active: ministral  # Change from qwen25coder
```

**Disable LLM entirely**:
```yaml
llm:
  enabled: false
```

**Adjust generation**:
```yaml
llm:
  generation:
    verbose: true  # Show token generation
  model:
    options:
      qwen25coder:
        max_tokens: 4096  # Increase for large repairs
```

**Customize prompts**: Edit `llm.prompts.classify` or `llm.prompts.repair_generic`

## Known Constraints

**LLM limitations**:
- Requires Apple Silicon Mac (mlx-lm dependency)
- First run downloads ~4-8GB model (cached after)
- Generation adds 1-3 seconds per repair

**Formatter requirements**:
- External tools (shfmt, prettier, etc.) must be in PATH
- Tools invoked via `bash -lc` to pick up shell environment

**Clipboard behavior**:
- pyperclip uses `pbcopy`/`pbpaste` on macOS
- May require accessibility permissions on some systems

## Troubleshooting

**LLM not loading**:
- Check HuggingFace cache: `~/.cache/huggingface/`
- Verify network for first-time model download
- Check active model exists in config: `llm.model.options.<active>`

**Formatter not found**:
- Install missing tool (e.g., `brew install shfmt`)
- Ensure tool is in PATH visible to `bash -lc`
- Run with `--no-llm` to skip LLM fallback

**Undo not working**:
- Check history file exists: `~/.clipfix_history.jsonl`
- Verify history has entries: `cat ~/.clipfix_history.jsonl`
- History only saved when clipboard actually changed

**Binary build fails**:
- Ensure PyOxidizer installed: `cargo install pyoxidizer`
- Check Python 3.10+ available
- Review `pyoxidizer.bzl` for path issues

## Production Deployment

**Recommended setup**:
1. Install Python dependencies: `pip install -e python`
2. Install optional formatters: `brew install shfmt prettier sqlfluff`
3. Pre-download LLM: Run `clipfix` once (triggers model download)
4. Add to PATH or create alias: `alias fix='clipfix'`

**Binary distribution**:
1. Build with PyOxidizer: `pyoxidizer build --release`
2. Distribute binary: `build/*/release/clipfix`
3. No Python runtime required on target system
4. LLM model must still be downloaded on first run

## Performance Considerations

**Fast path** (no LLM):
- JSON, YAML: <100ms (pure Python)
- External formatters: 100-300ms (subprocess overhead)

**Slow path** (LLM enabled):
- First classification: 1-3s (model load + inference)
- Subsequent calls: 0.5-1s (model cached)
- Repair: 2-5s (generates full code response)

**Optimization tips**:
- Use `--no-llm` for known-good code
- Pre-format with external tools before clipboard
- Keep clipboard content small (<1000 lines)
