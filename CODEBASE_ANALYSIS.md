# eClipLint Codebase Functionality Analysis

## Table of Contents
1. [Overview](#overview)
2. [How It Works](#how-it-works)
3. [Agent System](#agent-system)
4. [System Prompts](#system-prompts)
5. [Language-Specific Differences](#language-specific-differences)
6. [Areas for Improvement](#areas-for-improvement)

---

## Overview

**eClipLint** is a clipboard-based code formatter with AI-powered repair capabilities. It reads code from your clipboard, detects the language, formats it using deterministic tools (black, prettier, shfmt, etc.), and falls back to AI repair when formatting fails.

### Core Philosophy
- **Quality over speed**: Deterministic formatters first, AI as fallback
- **Transparency**: Show users what changed (--diff mode, change summaries)
- **Local processing**: All AI runs locally via mlx-lm (no cloud, no data transmission)
- **Community-editable**: Repair prompts stored in JSON files (no code changes needed)

---

## How It Works

### Full Pipeline (Step-by-Step)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. CLIPBOARD INPUT                                              │
│    pyperclip.paste() → raw text                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. SEGMENTATION (segmenter.py)                                  │
│    Detect structure:                                            │
│    • Markdown fences: ```python ... ```                         │
│    • Bash heredocs: python - <<'PY' ... PY                      │
│    • Raw code (no wrapper)                                      │
│                                                                  │
│    Output: List of Segment objects with:                        │
│    - kind: "markdown_fence" / "bash_python_heredoc" / "raw"     │
│    - text: actual code content                                  │
│    - prefix/suffix: wrappers to preserve                        │
│    - inner_kind: detected language (if known)                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. CLASSIFICATION (detect_and_format.py)                        │
│    Per segment, detect language:                                │
│                                                                  │
│    A. Heuristic detection (_detect_kind):                       │
│       - Check for imports (Python: "import ", "from ... import")│
│       - Try parsing as JSON                                     │
│       - Check for shebang/keywords (Bash: "#!/bin/bash")        │
│       - Check for function signatures (Rust: "fn main")         │
│       - Check for type annotations (TypeScript: ": string")     │
│       - Check for SQL keywords ("SELECT", "JOIN", "WHERE")      │
│       - Default: "python"                                       │
│                                                                  │
│    B. LLM classification (if ambiguous and allow_llm=True):     │
│       - Call llm_classify() with code snippet                   │
│       - LLM returns JSON: {"kind": "python"}                    │
│       - Used when heuristic fails or returns "unknown"/"raw"    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. FORMATTING ATTEMPT (detect_and_format.py)                    │
│    Try deterministic formatter based on language:               │
│                                                                  │
│    Python:   ruff format → black → dedent (fallback)            │
│    JavaScript: prettier --parser babel                          │
│    TypeScript: prettier --parser typescript                     │
│    Bash:     shfmt -w -i 2 -ci                                  │
│    SQL:      sqlfluff fix --dialect postgres                    │
│    Rust:     rustfmt                                            │
│    JSON:     json.dumps(indent=2)                               │
│    YAML:     ruamel.yaml                                        │
│                                                                  │
│    If formatter succeeds → DONE (return formatted code)         │
│    If formatter fails → Go to step 5                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. AI REPAIR (if allow_llm=True and formatting failed)          │
│    Call llm_repair(language, code):                             │
│                                                                  │
│    A. Get ManagerAgent instance (lazy-loaded, singleton)        │
│    B. ManagerAgent routes to specialist agent:                  │
│       - PythonAgent (loads knowledge/python.json)               │
│       - JavaScriptAgent (loads knowledge/javascript.json)       │
│       - BashAgent (loads knowledge/bash.json)                   │
│       - SQLAgent (loads knowledge/sql.json)                     │
│       - RustAgent (loads knowledge/rust.json)                   │
│       - GenericAgent (fallback, minimal prompt)                 │
│                                                                  │
│    C. Agent.repair(code):                                       │
│       - Load repair_prompt from JSON knowledge                  │
│       - Insert code into prompt template: {code} placeholder    │
│       - Apply chat template (if model supports it)              │
│       - Generate with mlx-lm (max_tokens=2048 default)          │
│       - Strip markdown fences from output                       │
│       - Return repaired code                                    │
│                                                                  │
│    D. Retry formatting on repaired code:                        │
│       - Call _format_code(language, repaired_code)              │
│       - If succeeds → mode = "repaired+formatted"               │
│       - If fails → error (repair couldn't fix it)               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. CLIPBOARD OUTPUT                                             │
│    If --diff: Show unified diff (colored), don't modify clipboard│
│    Else:                                                        │
│    - Save original to history (for --undo)                      │
│    - Write formatted/repaired code to clipboard                 │
│    - Show summary: "✓ ecliplint: repaired+formatted (3 lines   │
│                     modified, 1 line added)"                    │
└─────────────────────────────────────────────────────────────────┘
```

### Key Files

| File | Purpose |
|------|---------|
| `main.py` | Entry point, CLI argument parsing, diff display |
| `detect_and_format.py` | Core pipeline: classification → formatting → repair |
| `segmenter.py` | Parse clipboard input (markdown fences, heredocs) |
| `llm.py` | LLM model loading, classification, repair orchestration |
| `history.py` | Undo functionality (JSON log of previous clipboards) |
| `agents/manager.py` | Route to language-specific specialist agents |
| `agents/base_agent.py` | Base class: load JSON knowledge, repair logic |
| `agents/*_agent.py` | Specialist agents (Python, JS, Bash, SQL, Rust, Generic) |
| `knowledge/*.json` | Language-specific prompts, error patterns, style rules |

---

## Agent System

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       ManagerAgent                          │
│  (routes based on detected language, lazy-loads agents)     │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────┴───────────────────┐
        │                                       │
┌───────▼──────┐  ┌──────────────┐  ┌─────────▼────────┐
│ PythonAgent  │  │ JavaScriptA. │  │   BashAgent      │
│              │  │              │  │                  │
│ knowledge/   │  │ knowledge/   │  │ knowledge/       │
│ python.json  │  │ javascript.  │  │ bash.json        │
└──────────────┘  │ json         │  └──────────────────┘
                  └──────────────┘
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│  SQLAgent    │  │  RustAgent   │  │  GenericAgent    │
│              │  │              │  │  (fallback)      │
│ knowledge/   │  │ knowledge/   │  │  (no JSON file)  │
│ sql.json     │  │ rust.json    │  │                  │
└──────────────┘  └──────────────┘  └──────────────────┘
```

### How Agents Work

**1. Lazy Loading**
- Agents are NOT created upfront
- ManagerAgent instantiates them only when first needed
- Subsequent requests reuse cached agent instance
- Example: First Python repair loads PythonAgent, all future Python repairs reuse it

**2. Shared Model**
- All agents share the same mlx-lm model instance
- Model loaded once (expensive: ~1-3s first time)
- Tokenizer shared across all agents
- No redundant model loading

**3. Knowledge-Based**
- Each agent loads a JSON file with:
  - `repair_prompt`: Detailed instructions for the LLM
  - `common_errors`: Patterns like "IndentationError", "SyntaxError"
  - `style_rules`: PEP 8, Standard Style, shellcheck guidelines
  - `test_cases`: Broken/fixed examples
  - `formatter_preferences`: Which tools to use (ruff, prettier, shfmt)

**4. Routing Logic** (manager.py:36-96)

```python
agent_map = {
    "python": PythonAgent,
    "javascript": JavaScriptAgent,
    "js": JavaScriptAgent,           # Alias
    "typescript": JavaScriptAgent,    # Reuses JS agent (similar syntax)
    "ts": JavaScriptAgent,
    "bash": BashAgent,
    "sh": BashAgent,
    "shell": BashAgent,
    "sql": SQLAgent,
    "postgres": SQLAgent,
    "postgresql": SQLAgent,
    "mysql": SQLAgent,
    "rust": RustAgent,
    "rs": RustAgent,
}

# Cache normalization: "js"/"typescript"/"ts" all use "javascript" cache key
```

**5. Agent Lifecycle**

```
Request 1 (Python):
  → ManagerAgent.repair("x=1", "python")
  → route() checks cache: "python" not found
  → Instantiate PythonAgent(model, tokenizer)
  → PythonAgent loads knowledge/python.json
  → Cache: agents["python"] = PythonAgent instance
  → Call agent.repair("x=1")
  → Return "x = 1"

Request 2 (Python):
  → ManagerAgent.repair("def foo", "python")
  → route() checks cache: "python" FOUND
  → Reuse cached PythonAgent
  → Call agent.repair("def foo")
  → Return "def foo():\n    pass"

Request 3 (JavaScript):
  → ManagerAgent.repair("const x=1", "javascript")
  → route() checks cache: "javascript" not found
  → Instantiate JavaScriptAgent(model, tokenizer)
  → JavaScriptAgent loads knowledge/javascript.json
  → Cache: agents["javascript"] = JavaScriptAgent instance
  → Call agent.repair("const x=1")
  → Return "const x = 1;"
```

---

## System Prompts

### Are Prompts Different Per Language?

**YES!** Each language has a completely different, specialized prompt. This is the core innovation of the multi-agent architecture.

### Prompt Structure

All prompts follow this template (from `base_agent.py:84-125`):

```python
# 1. Load prompt template from JSON
prompt_template = knowledge["repair_prompt"]

# 2. Insert actual broken code
prompt = prompt_template.format(code=broken_code)

# 3. Apply chat template (if model supports it)
if tokenizer.chat_template:
    prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}],
        add_generation_prompt=True
    )

# 4. Generate with mlx-lm
repaired = generate(model, tokenizer, prompt=prompt, max_tokens=2048)

# 5. Strip markdown fences
return _strip_fences(repaired)
```

### Example: Python Prompt (knowledge/python.json)

```
You are an expert Python developer specializing in code repair and PEP 8 compliance.

Your mission: Fix syntax errors and apply modern Python best practices.

## Common Syntax Errors to Fix

1. **IndentationError**: Use exactly 4 spaces per indent level (never tabs)
   - Example: `if x:\n    print(x)` not `if x:\nprint(x)`

2. **Missing colons**: Add `:` after if/for/while/def/class/try/except/with statements
   - Example: `if x > 0:` not `if x > 0`

3. **Quote consistency**: Fix mixed quotes, prefer single quotes for strings
   - Example: `'hello'` not `"hello"` (unless string contains apostrophe)

... (continues with detailed PEP 8 rules, spacing, naming conventions, f-strings)

## Critical Rules

1. **Preserve original logic**: Do NOT change what the code does
2. **Keep variable names**: Do NOT rename unless fixing obvious typos
3. **Minimal changes**: Fix only what's broken, don't over-refactor
4. **Output only code**: No explanations, no markdown, no comments about changes
5. **Valid Python**: Output must be syntactically correct and executable

## Input Code

```python
x=1
 if x>0:
print(x)
```

## Fixed Code

Provide ONLY the corrected Python code below:
```

### Example: JavaScript Prompt (knowledge/javascript.json)

```
You are an expert JavaScript developer specializing in modern ES6+ code repair.

Your mission: Fix syntax errors and apply JavaScript Standard Style best practices.

## Common Syntax Errors to Fix

1. **Missing semicolons**: Add where appropriate (consistent style)
   - If code uses semicolons, add missing ones
   - If code omits semicolons, keep consistent (ASI-safe)

2. **Bracket matching**: Close all opening brackets/braces/parens
   - `{ }` for objects and blocks
   - `[ ]` for arrays
   - `( )` for function calls and parameters

... (continues with arrow functions, const/let/var, template literals)

## Modern JavaScript Best Practices

- **Naming conventions**:
  - camelCase for variables and functions: `userName`, `getUserData`
  - PascalCase for classes: `UserAccount`, `APIHandler`
  - UPPER_CASE for constants: `MAX_RETRIES`, `API_URL`

... (continues with spacing, indentation, modern syntax)

## Input Code

```javascript
const x=1
if(x>0){
console.log(x)
}
```

## Fixed Code

Provide ONLY the corrected JavaScript code below:
```

### Example: Bash Prompt (knowledge/bash.json)

```
You are an expert in Bash scripting and shell best practices.

Your mission: Fix syntax errors and apply shellcheck-recommended best practices.

## Common Syntax Errors to Fix

1. **Missing spaces in conditionals**: Spaces required around `[` and `]`
   - Correct: `if [ "$x" = "1" ]; then`
   - Incorrect: `if ["$x" = "1"]; then`

2. **Unquoted variables**: Quote variables to prevent word splitting
   - Correct: `echo "$var"`
   - Incorrect: `echo $var`

... (continues with missing then/do, command substitution, set -euo pipefail)

## Input Code

```bash
if [$x -eq 1]
then
echo $x
fi
```

## Fixed Code

Provide ONLY the corrected Bash code below:
```

---

## Language-Specific Differences

### Prompt Differences Summary

| Language | Focus | Key Rules | Style Guide |
|----------|-------|-----------|-------------|
| **Python** | PEP 8 compliance, indentation (4 spaces), colons | • Use f-strings<br>• snake_case vars<br>• PascalCase classes<br>• Fix IndentationError<br>• Add missing imports | PEP 8, Black (88 char) |
| **JavaScript** | ES6+ syntax, semicolons, const/let | • Use const/let (not var)<br>• Template literals<br>• Arrow functions<br>• camelCase vars<br>• 2 space indent | JavaScript Standard Style |
| **Bash** | Shellcheck rules, quoting, conditionals | • Quote all variables<br>• Use [[ ]] not [ ]<br>• $(cmd) not backticks<br>• set -euo pipefail<br>• 2 space indent | Shellcheck recommendations |
| **SQL** | PostgreSQL dialect, formatting | • Uppercase keywords<br>• Lowercase identifiers<br>• JOIN optimization<br>• Indentation | PostgreSQL style |
| **Rust** | Rustfmt style, ownership hints | • snake_case vars<br>• CamelCase types<br>• Explicit lifetimes<br>• Error handling | Rustfmt defaults |
| **YAML/JSON** | Syntax correctness | • Proper indentation<br>• Quote consistency<br>• Valid structure | - |

### Common Errors Per Language

**Python** (from knowledge/python.json:8-41):
- IndentationError (4 spaces required)
- SyntaxError (missing colons)
- NameError (undefined variables/imports)
- TabError (mixed tabs/spaces)

**JavaScript** (from knowledge/javascript.json:7-32):
- SyntaxError (missing brackets/braces)
- Missing parentheses in function calls
- ReferenceError (undefined variables)

**Bash** (from knowledge/bash.json:7-32):
- Missing spaces around [ ]
- Unquoted variables
- Missing fi/done/esac
- Unbound variables (set -u)

### Test Cases in Knowledge Files

Each language includes broken/fixed examples:

**Python test case**:
```json
{
  "broken": "x=1\n if x>0:\nprint(x)",
  "fixed": "x = 1\nif x > 0:\n    print(x)",
  "errors": ["spacing around =", "incorrect indentation", "spacing around >"]
}
```

**JavaScript test case**:
```json
{
  "broken": "const x=1\nif(x>0){\nconsole.log(x)\n}",
  "fixed": "const x = 1;\nif (x > 0) {\n  console.log(x);\n}",
  "errors": ["missing spaces", "missing semicolons"]
}
```

**Bash test case**:
```json
{
  "broken": "if [$x -eq 1]\nthen\necho $x\nfi",
  "fixed": "if [ \"$x\" -eq 1 ]; then\n  echo \"$x\"\nfi",
  "errors": ["missing spaces around [", "unquoted variable"]
}
```

---

## Areas for Improvement

### 1. Testing & Quality Assurance

**Current state**: No automated tests for agent repair quality

**Improvements**:
- [ ] **Automated test suite using test_cases from JSON**
  - Each knowledge/*.json has test_cases array
  - Create pytest tests that feed "broken" code to agent
  - Assert output matches "fixed" code (or passes formatter)
  - Run on every commit (CI/CD)

- [ ] **Regression tests for known failures**
  - When users report broken repairs, add to test suite
  - Prevent regressions in future releases

- [ ] **Formatter availability detection**
  - Warn user if formatter missing: "Install ruff for better Python formatting"
  - Suggest `pip install ruff` / `npm install -g prettier`

**Implementation**:
```python
# tests/test_agents.py
import json
from pathlib import Path
from clipfix.engines.agents.manager import ManagerAgent
from clipfix.engines.llm import _load_model

def test_python_agent_repairs():
    model, tokenizer = _load_model()
    manager = ManagerAgent(model, tokenizer)

    knowledge = json.loads(Path("knowledge/python.json").read_text())

    for test_case in knowledge["test_cases"]:
        repaired = manager.repair(test_case["broken"], "python")
        # Either matches expected fix, or passes formatter
        assert repaired == test_case["fixed"] or _format_passes(repaired, "python")
```

### 2. Performance Optimizations

**Current state**: Model loads on first LLM use (~1-3s), each repair takes 2-5s

**Improvements**:
- [ ] **Formatter caching**
  - Cache formatter availability checks (_has_cmd results)
  - Currently checks `command -v ruff` on every format attempt
  - Cache for session duration

- [ ] **Streaming LLM output**
  - Show repair progress in real-time
  - Currently: "🔧 Repairing python code..." (blocking)
  - Improved: "🔧 Repairing: `def fo` → `def foo` → `def foo():` ..." (streaming)

- [ ] **Parallel segment processing**
  - If clipboard has multiple fenced blocks, repair in parallel
  - Currently: Sequential (segment 1 → segment 2 → segment 3)
  - Improved: All segments repaired simultaneously (use threading)

**Implementation**:
```python
# Formatter caching (llru_cache)
from functools import lru_cache

@lru_cache(maxsize=20)
def _has_cmd(cmd: str) -> bool:
    return subprocess.call(["bash","-lc", f"command -v {cmd} >/dev/null 2>&1"]) == 0

# Streaming (mlx-lm supports this)
def repair_streaming(self, code: str):
    for token in generate_step(self.model, self.tokenizer, prompt):
        print(token, end="", flush=True)  # Show token-by-token
    print(" ✓")
```

### 3. User Experience Enhancements

**Current state**: CLI-only, basic progress feedback

**Improvements**:
- [ ] **Interactive mode**
  - `ecliplint --watch`: Monitor clipboard, auto-format on change
  - Daemonize process, format whenever clipboard changes
  - Notification: "Code formatted" (macOS native notification)

- [ ] **Multi-level undo**
  - Currently: `--undo` restores previous (1 level)
  - Improved: `--undo 3` to go back 3 changes
  - `--undo --list` to browse history with timestamps

- [ ] **Diff improvements**
  - Currently: Unified diff with ANSI colors
  - Improved: Side-by-side diff (`diff-so-fancy` style)
  - Highlight exact characters changed (not just lines)

- [ ] **Configuration file**
  - `~/.ecliplint/config.yaml`: User preferences
  - Disable specific formatters: `formatters: { python: [ruff] }` (skip black)
  - Custom max_tokens per language
  - Default to --diff mode (always preview first)

**Implementation**:
```yaml
# ~/.ecliplint/config.yaml
defaults:
  mode: diff  # Always preview first
  max_history: 50

formatters:
  python: [ruff]  # Only use ruff, skip black
  javascript: [prettier]

agents:
  python:
    max_tokens: 4096  # Override default 2048
```

### 4. Knowledge Base Improvements

**Current state**: 7 language JSON files, manually curated

**Improvements**:
- [ ] **Community contributions**
  - GitHub Issues template: "Broken repair example"
  - Users submit broken/fixed pairs
  - Maintainers add to test_cases in JSON

- [ ] **Automatic prompt optimization**
  - Track which prompts lead to successful repairs
  - A/B test prompt variations
  - Metrics: formatter_pass_rate after repair

- [ ] **More languages**
  - Go (knowledge/go.json + go_agent.py)
  - C/C++ (knowledge/c.json + c_agent.py)
  - Java (knowledge/java.json + java_agent.py)
  - Ruby (knowledge/ruby.json + ruby_agent.py)
  - PHP (knowledge/php.json + php_agent.py)

- [ ] **Dialect support**
  - SQL: MySQL vs PostgreSQL vs SQLite (different syntax)
  - Bash: POSIX sh vs bash vs zsh
  - Python: 2.7 vs 3.x (currently assumes 3.10+)

**Implementation**:
```json
// knowledge/go.json
{
  "language": "go",
  "repair_prompt": "You are a Go expert. Fix syntax errors and apply gofmt style...",
  "common_errors": [
    {
      "type": "SyntaxError",
      "pattern": "expected '}', found 'EOF'",
      "fix": "Close all opening braces"
    }
  ],
  "formatter_preferences": {
    "primary": "gofmt",
    "secondary": "goimports"
  }
}
```

### 5. Advanced Features

**Improvements**:
- [ ] **Plugin system**
  - Allow custom formatters: `~/.ecliplint/plugins/my_formatter.py`
  - Hook into pipeline: custom_segment, custom_format, custom_repair

- [ ] **Context-aware repair**
  - If clipboard is from GitHub issue, preserve markdown structure
  - If from terminal error message, extract just the code

- [ ] **Explain mode**
  - `ecliplint --explain`: Show what was fixed and why
  - Output: "Fixed IndentationError on line 2: Added 4 spaces"

- [ ] **Confidence scoring**
  - Agent returns confidence: "90% certain this is correct"
  - If low confidence, ask user to review

- [ ] **Multi-language segments**
  - Detect multiple languages in one clipboard
  - Example: HTML with embedded JavaScript and CSS
  - Repair each language separately

**Implementation**:
```python
# --explain mode
def repair_with_explanation(self, code: str) -> tuple[str, list[str]]:
    # Modify prompt to request explanations
    prompt = self.knowledge["repair_prompt"].format(code=code)
    prompt += "\n\nAlso provide a brief explanation of each fix."

    repaired, explanations = llm_generate_with_explanation(prompt)
    return repaired, explanations

# Usage
repaired, explanations = agent.repair_with_explanation("x=1\n if x>0:\nprint(x)")
# Output:
# repaired = "x = 1\nif x > 0:\n    print(x)"
# explanations = [
#   "Line 1: Added spaces around = operator",
#   "Line 2: Removed incorrect indentation before 'if'",
#   "Line 3: Added 4-space indentation for print statement"
# ]
```

### 6. Cross-Platform Support

**Current state**: macOS only (Apple Silicon, mlx-lm)

**Improvements**:
- [ ] **Intel Mac support**
  - Use alternative LLM backend (transformers + CPU)
  - Slower but functional

- [ ] **Linux support**
  - Use transformers + CUDA (if NVIDIA GPU)
  - Use transformers + CPU (fallback)
  - Different clipboard library (xclip, xsel)

- [ ] **Windows support**
  - Use transformers + CPU/CUDA
  - Windows clipboard API

**Implementation**:
```python
# llm.py - Platform detection
import platform
import sys

def _get_llm_backend():
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        # Apple Silicon - use mlx
        from mlx_lm import load, generate
        return "mlx"
    elif torch.cuda.is_available():
        # NVIDIA GPU - use transformers + CUDA
        from transformers import AutoModel, AutoTokenizer
        return "transformers-cuda"
    else:
        # CPU fallback
        from transformers import AutoModel, AutoTokenizer
        return "transformers-cpu"
```

### 7. Documentation & Onboarding

**Improvements**:
- [ ] **Video tutorials**
  - YouTube: "eClipLint in 60 seconds"
  - Show hotkey setup, --diff mode, undo

- [ ] **Interactive tutorial**
  - `ecliplint --tutorial`: Step-by-step guide
  - Copy broken code → run ecliplint → see result

- [ ] **Troubleshooting guide**
  - Common errors with solutions
  - "Model download failed" → Check disk space
  - "Formatter not found" → Install ruff/prettier

- [ ] **API documentation**
  - For developers wanting to integrate eClipLint
  - Example: Use as Python library (not just CLI)

**Implementation**:
```python
# Python API usage (not just CLI)
from clipfix.engines.detect_and_format import process_text

broken_code = "x=1\n if x>0:\nprint(x)"
success, fixed_code, mode = process_text(broken_code, allow_llm=True)

if success:
    print(f"Fixed ({mode}):\n{fixed_code}")
else:
    print(f"Failed: {mode}")
```

---

## Summary

**eClipLint's Strengths**:
- ✅ Quality-first: Deterministic formatters before AI
- ✅ Transparency: --diff mode, change summaries
- ✅ Privacy: Fully local processing (no cloud)
- ✅ Extensibility: JSON knowledge files (easy to edit)
- ✅ Multi-agent: Language specialists (not generic AI)

**Key Improvements Needed**:
1. **Testing**: Automated test suite using JSON test_cases
2. **Performance**: Formatter caching, streaming output, parallel processing
3. **UX**: Watch mode, multi-level undo, interactive diff
4. **Knowledge**: More languages (Go, C++, Java, Ruby, PHP)
5. **Cross-platform**: Intel Mac, Linux, Windows support
6. **Advanced**: Plugin system, explain mode, confidence scoring

**Most Impactful Next Steps** (prioritized):
1. **Automated testing** (prevents regressions, builds trust)
2. **Watch mode** (killer feature: auto-format on clipboard change)
3. **More languages** (broader appeal: Go, C++, Java)
4. **Cross-platform** (expand user base beyond Apple Silicon)

---

**Generated**: 2024-12-13
**Version**: eClipLint v1.0.0
**Contact**: https://github.com/deesatzed/eClipLint/issues
