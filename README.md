# eClipLint

**Intelligent clipboard code formatter with AI-powered repair**

> Clipboard in → fixed code out → clipboard

Transform messy code snippets from Stack Overflow, documentation, or chat into clean, formatted code — automatically.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: macOS](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](https://www.apple.com/macos/)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

---

## What is eClipLint?

eClipLint is a **quality-first clipboard code formatter** for macOS that:

1. **Reads code from your clipboard**
2. **Detects the language** (Python, JavaScript, Bash, SQL, Rust, etc.)
3. **Formats with deterministic tools** (black, prettier, shfmt, rustfmt, sqlfluff)
4. **Repairs with AI when formatting fails** (language-specific specialist agents)
5. **Writes clean code back to clipboard**

All in **<1 second** for valid code, or **2-5 seconds** with AI repair.

---

## Why eClipLint?

**Problem**: You copy code from Stack Overflow, documentation, or chat. It has:
- Incorrect indentation
- Syntax errors from incomplete selection
- Mixed formatting styles
- Missing semicolons/quotes

**Solution**: Run `ecliplint` (or set up a hotkey). Paste perfect code.

**Difference from IDEs**: Works **across all applications** (browser, terminal, chat, notes) — not just in your editor.

---

## Key Features

### 🎯 Multi-Agent AI Architecture
- **7 language specialist agents** with dedicated knowledge bases
- **Python**: PEP 8 expert with indentation, naming, f-string guidance
- **JavaScript/TypeScript**: ES6+ with Standard Style best practices
- **Bash**: Shellcheck-recommended patterns, quoting rules
- **SQL**: PostgreSQL dialect with JOIN optimization
- **Rust**: Rustfmt style with ownership hints
- **YAML/JSON**: Syntax and formatting rules

### 🔍 Preview Mode
```bash
ecliplint --diff  # Show what will change (without modifying clipboard)
```
- See colored diff before applying
- Review AI suggestions
- Non-destructive workflow

### 📊 Progress Feedback
No more wondering if it's frozen:
```
⏳ Loading model... ✓
🔧 Repairing python code... ✓
✓ ecliplint: repaired+formatted (3 lines modified, 1 line added)
```

### 🔄 Undo Support
```bash
ecliplint --undo  # Restore previous clipboard (up to 25 history)
```

### 🎨 Community-Editable Knowledge
Improve repair quality by editing JSON files (no code changes needed):
- `knowledge/python.json` - PEP 8 rules, common errors
- `knowledge/javascript.json` - ES6+ patterns
- `knowledge/bash.json` - Shellcheck rules
- See all in `knowledge/` directory

---

## Installation

### Requirements
- **macOS 13+** (Apple Silicon)
- **Python 3.10+**

### Quick Install
```bash
git clone https://github.com/deesatzed/eClipLint.git
cd eClipLint
pip install -e python
ecliplint --help
```

### Optional (Recommended): Install Formatters
```bash
# Python
pip install black ruff

# JavaScript/TypeScript
npm install -g prettier

# Bash
brew install shfmt

# SQL
pip install sqlfluff

# Rust
rustup component add rustfmt
```

eClipLint works without these, but they improve formatting quality.

---

## Quick Start

### Example 1: Format JSON
```bash
# Copy to clipboard:
{"a":1,"b":2,"c":3}

# Run:
ecliplint

# Paste:
{
  "a": 1,
  "b": 2,
  "c": 3
}
```

### Example 2: Fix Broken Python
```bash
# Copy to clipboard:
x=1
 if x>0:
print(x)

# Run:
ecliplint

# See:
🔧 Repairing python code... ✓
✓ ecliplint: repaired+formatted (2 lines modified)

# Paste:
x = 1
if x > 0:
    print(x)
```

### Example 3: Preview Changes (--diff)
```bash
# Copy broken code, then:
ecliplint --diff

# Output:
--- before
+++ after
@@ -1,3 +1,3 @@
-x=1
- if x>0:
-print(x)
+x = 1
+if x > 0:
+    print(x)

# Clipboard UNCHANGED (review first, then run without --diff)
```

### Example 4: SQL Formatting
```bash
# Copy:
select id,name,email from users where active=1

# Run:
ecliplint

# Paste:
SELECT
  id,
  name,
  email
FROM users
WHERE active = 1;
```

---

## Usage

### Basic Commands
```bash
ecliplint              # Format clipboard
ecliplint --diff       # Preview changes (don't modify clipboard)
ecliplint --undo       # Restore previous clipboard
ecliplint --no-llm     # Disable AI repair (formatters only)
ecliplint --help       # Show all options
```

### New in v1.2: UX Improvements
```bash
ecliplint --lang python        # Force specific language
ecliplint --health             # Check formatter installation
ecliplint --cache-stats        # View detailed cache metrics
```

### Flags
- `--diff` - Show changes without modifying clipboard
- `--undo` - Restore previous clipboard from history
- `--no-llm` - Disable AI fallback (fast, but fails on broken code)
- `--lang LANGUAGE` - Force specific language (python, javascript, bash, sql, rust, json, yaml)
- `--health` - Check formatter installation status
- `--cache-stats` - Show detailed cache statistics with hit rates and time saved
- `--parallel` - Manually enable parallel processing (auto-enabled for 3+ segments)
- `--benchmark` - Show performance timing
- `--max-history N` - Set undo history depth (default: 25)

---

## Supported Languages

| Language   | Formatter     | AI Agent | Status |
|------------|---------------|----------|--------|
| Python     | ruff / black  | ✅       | Excellent |
| JavaScript | prettier      | ✅       | Excellent |
| TypeScript | prettier      | ✅       | Excellent |
| Bash       | shfmt         | ✅       | Excellent |
| SQL        | sqlfluff      | ✅       | Good |
| Rust       | rustfmt       | ✅       | Good |
| YAML       | ruamel.yaml   | ✅       | Good |
| JSON       | json stdlib   | ✅       | Excellent |

**AI Agent**: Language-specific specialist with dedicated repair prompts and common error knowledge.

---

## How It Works

### 1. Segmentation
Detects structure:
- Bash heredocs with embedded Python: `python - <<'PY' ... PY`
- Markdown fences: ` ```python ... ``` `
- Raw code

### 2. Classification
Heuristic detection (fast):
- Checks for `import`, `function`, `SELECT`, etc.
- Falls back to AI classification if ambiguous

### 3. Formatting
Tries deterministic formatters first:
- Python: `ruff format` → `black` → dedent
- JavaScript: `prettier`
- Bash: `shfmt`
- SQL: `sqlfluff`
- JSON: stdlib `json.dumps`

### 4. AI Repair (if formatting fails)
Routes to language specialist agent:
- **PythonAgent**: Loads `knowledge/python.json`
- Uses PEP 8 rules, common error patterns
- Repairs with mlx-lm (local, no network)
- Retries formatter on repaired code

### 5. Clipboard Update
- Saves original to history (for --undo)
- Writes formatted code
- Shows change summary

---

## New Performance Features (v1.1)

> **Inspired by [qlty](https://github.com/qlty-check/qlty)** - We analyzed qlty's architecture and adapted their best patterns (parallel processing, caching, plugin system) for clipboard-focused formatting. See [QLTY_IMPROVEMENTS.md](QLTY_IMPROVEMENTS.md) for full analysis.

### 🚀 Parallel Processing
- **3-10x faster** for multi-segment code
- Processes Python, JavaScript, SQL simultaneously
- Enable with `--parallel` flag
- *Inspired by qlty's Rust rayon parallel execution*

### 💾 Result Caching
- **100x faster** for repeated formatting
- 24-hour TTL with smart eviction
- `--cache-stats` to view statistics
- `--clear-cache` to reset
- *Adapted from qlty's content-based caching strategy*

### 🔌 Plugin System
- Add custom formatters via TOML files
- No code changes needed
- See `plugins/examples/` for templates
- *Inspired by qlty's TOML-based plugin definitions*

### Performance Benchmarks
```bash
ecliplint --benchmark  # Show timing
ecliplint --parallel   # Use parallel mode
ecliplint --cache-stats # View cache hit rate
```

**Architecture improvements from qlty**: We extracted high-value patterns while avoiding bloat. Unlike qlty's 70+ linters, we focus on 7 core languages. No cloud integration, no git features - just fast, local clipboard formatting.

---

## v1.2: 80/20 UX Enhancements

Four high-value improvements that deliver 80% of user benefit with minimal complexity:

### 1. 🧠 Smart Auto-Parallel
**Before**: Had to remember `--parallel` flag
**Now**: Auto-enables for 3+ segments

```bash
# Copy multi-language code → automatically uses parallel processing
ecliplint  # That's it!
```

### 2. 🎯 Language Override
**Before**: Relied on auto-detection
**Now**: Force specific language when needed

```bash
# When detection is wrong or you know the language:
ecliplint --lang python    # Force Python formatting
ecliplint --lang sql       # Force SQL formatting
```

**Use cases**:
- Ambiguous code snippets
- Plain text that should be treated as code
- Override when detection fails

### 3. 🏥 Formatter Health Check
**Before**: Trial and error to see what's installed
**Now**: Instant status check

```bash
ecliplint --health

# Output:
# ✓ black (Python) installed
# ✓ prettier (JavaScript/TypeScript) installed
# ✗ shfmt (Bash) not found
#   Install: brew install shfmt
```

**Benefits**:
- Quick diagnostic
- Installation instructions included
- See which languages are fully supported

### 4. 📊 Enhanced Cache Stats
**Before**: Basic entry count
**Now**: Hit rate, time saved, top languages

```bash
ecliplint --cache-stats

# Output:
# Entries: 42
# Hit rate: 67.3%
# Time saved: ~105s
# Top cached languages:
#   python: 15 times
#   javascript: 12 times
```

**Insights**:
- See actual performance gains
- Understand usage patterns
- Measure cache effectiveness

---

## Architecture

### Multi-Agent System
```
ManagerAgent (router)
    ↓
    ├─> PythonAgent      (knowledge/python.json)
    ├─> JavaScriptAgent  (knowledge/javascript.json)
    ├─> BashAgent        (knowledge/bash.json)
    ├─> SQLAgent         (knowledge/sql.json)
    ├─> RustAgent        (knowledge/rust.json)
    └─> GenericAgent     (fallback)
```

Each agent:
- Loads language-specific knowledge from JSON
- Uses tailored prompts with examples
- Shares same LLM model (lazy-loaded)

### Knowledge JSON Structure
```json
{
  "language": "python",
  "repair_prompt": "Detailed instructions with examples...",
  "common_errors": [
    {"type": "IndentationError", "fix": "...", "example": "..."}
  ],
  "style_rules": ["PEP 8: Use snake_case...", "..."],
  "test_cases": [{"broken": "...", "fixed": "..."}]
}
```

---

## Configuration

### LLM Model
Edit `config/llm.yaml` to change model:
```yaml
llm:
  enabled: true
  model:
    active: qwen25coder  # or ministral
    options:
      qwen25coder:
        repo: mlx-community/Qwen2.5-Coder-7B-Instruct-4bit
        max_tokens: 2048
```

### Disable AI Entirely
```yaml
llm:
  enabled: false  # Only use formatters, no AI
```

Or use `--no-llm` flag on command line.

---

## First-Time Setup

On first run, eClipLint downloads a **4GB AI model** (one-time):

```
⚠ First-time setup: Downloading mlx-community/Qwen2.5-Coder-7B-Instruct-4bit (~4GB)...
  This will take 1-5 minutes. Subsequent runs will be fast.
```

**Subsequent runs**: Model loads from cache in <1 second.

---

## Contributing

### Improve Repair Quality (Easy!)
Edit knowledge JSON files (no code changes needed):

```bash
# Edit language-specific knowledge:
vim knowledge/python.json      # Add PEP 8 rules, common errors
vim knowledge/javascript.json  # Add ES6+ patterns
vim knowledge/bash.json        # Add shellcheck rules

# Test your changes:
ecliplint  # Uses updated JSON automatically

# Submit PR:
git commit -m "Improve Python indentation repair"
```

### Add New Language
1. Create `knowledge/yourlanguage.json` (copy existing template)
2. Create `python/clipfix/engines/agents/yourlanguage_agent.py`:
   ```python
   from .base_agent import BaseAgent

   class YourLanguageAgent(BaseAgent):
       def __init__(self, model, tokenizer):
           super().__init__(model, tokenizer, language="yourlanguage")
   ```
3. Add to `manager.py` routing map
4. Test and submit PR

### Report Issues
Found a repair that didn't work? [Open an issue](https://github.com/deesatzed/eClipLint/issues) with:
- Broken code (clipboard input)
- Expected output
- Actual output

We'll improve the knowledge base!

---

## Troubleshooting

### "Clipboard access denied"
```bash
# Grant accessibility permissions:
# System Settings → Privacy & Security → Accessibility → Terminal (enable)
```

### "Model download fails"
```bash
# Check network connection
# Check available disk space (need 5GB free)
# Retry - download resumes from where it stopped
```

### "Formatter not found"
```bash
# Install missing formatter:
pip install black ruff  # Python
npm install -g prettier # JavaScript
brew install shfmt      # Bash
```

### "Intel Mac not supported"
eClipLint uses mlx-lm (Apple Silicon only). Intel Mac support planned for v2.0 with alternative LLM backend.

### "Code still broken after repair"
AI can't fix all errors (e.g., semantic errors, missing imports). Open an issue with the code sample — we'll improve the knowledge base.

---

## Performance

| Scenario | Time |
|----------|------|
| JSON formatting (no AI) | <100ms |
| Python formatting (valid code) | 100-300ms |
| AI classification | 500ms-1s |
| AI repair | 2-5s |
| First-time model load | 1-3s |
| First-time model download | 1-5 min |

**Optimization tip**: Use `--no-llm` for known-valid code (instant formatting).

---

## Roadmap

### v1.1 (qlty-inspired improvements)
- **Parallel processing** for multi-segment code (3-10x speedup)
- **Content-based caching** for repeated operations (100x speedup)
- **Plugin architecture** for custom formatters
- Automated test suite
- Better error messages and benchmarking
- Credits: Architecture patterns adapted from [qlty](https://github.com/qlty-check/qlty)

### v1.2 (80/20 UX improvements) ✅
- **Smart auto-parallel** - Auto-enables for 3+ segments
- **Language override** (`--lang`) - Force specific language
- **Formatter health check** (`--health`) - Diagnostic tool
- **Enhanced cache stats** - Hit rate, time saved, top languages
- 3 hours development time, 80% of value improvement

### v2.0
- Linux support (alternative LLM backend)
- Multi-level undo (history browser)
- Watch mode (auto-format on clipboard change)
- Streaming LLM output (show repair in progress)
- Plugin system for custom formatters

---

## FAQ

**Q: Does this send my code to the cloud?**
A: **No.** eClipLint uses a local AI model (mlx-lm). All processing is on-device. No network after initial model download.

**Q: How is this different from pasting into ChatGPT?**
A: eClipLint is **instant** (hotkey → formatted), uses **language specialists** with dedicated knowledge, and is **fully local**. No context switching, no copy-paste-copy workflow.

**Q: Can I use this in my company?**
A: Yes. MIT license. All processing is local (no data transmission). Safe for proprietary code.

**Q: Does it work with proprietary/internal languages?**
A: You can create a custom agent + knowledge JSON. If your language has a formatter, eClipLint can integrate it.

**Q: Why Apple Silicon only?**
A: mlx-lm is Apple's ML framework (fast, low memory). Intel support coming in v2.0 with alternative backend.

**Q: Can I customize the repair prompts?**
A: Yes! Edit `knowledge/*.json` files. Changes take effect immediately (no restart needed).

---

## License

MIT License - see [LICENSE](LICENSE) file

---

## Acknowledgments

- **[qlty](https://github.com/qlty-check/qlty)** - Inspired our v1.1 performance improvements (parallel processing, caching, plugin architecture)
- **mlx-lm** - Apple's ML framework
- **Qwen2.5-Coder** - AI model for code repair
- **black**, **prettier**, **shfmt**, **rustfmt**, **sqlfluff** - Formatter tools
- Community contributors to knowledge bases

---

## Support

- **Issues**: [GitHub Issues](https://github.com/deesatzed/eClipLint/issues)
- **Discussions**: [GitHub Discussions](https://github.com/deesatzed/eClipLint/discussions)
- **Contributions**: PRs welcome! (especially knowledge JSON improvements)

---

**Made with quality over speed**
*Because first impressions matter*
