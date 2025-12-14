# eClipLint Configuration Guide

Complete guide to configuring eClipLint for local and cloud modes.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Configuration Files](#configuration-files)
3. [Environment Variables](#environment-variables)
4. [Cloud Mode Setup](#cloud-mode-setup)
5. [Learning System](#learning-system)
6. [Cost Management](#cost-management)
7. [Hotkey Configuration](#hotkey-configuration)
8. [Advanced Settings](#advanced-settings)
9. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Local Mode (Default - No Configuration Required)

eClipLint works out of the box with local mode:

```bash
# Install
pip install ecliplint

# Initialize (downloads local model)
ecliplint --init

# Use immediately
echo "def foo(x=1 y=2" | pbcopy
ecliplint
pbpaste  # → def foo(x=1, y=2):
```

**No API key needed. 100% private.**

### 2. Cloud Mode (Optional - For Non-Proprietary Code)

To use powerful cloud models:

```bash
# 1. Get OpenRouter API key
#    https://openrouter.ai/keys

# 2. Create .env file
cp .env.example .env

# 3. Add your API key to .env
echo "OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE" >> .env

# 4. Enable cloud mode
ecliplint --enable-cloud

# 5. Test
echo "def foo(x=1 y=2" | pbcopy
ecliplint --cloud
pbpaste  # → def foo(x=1, y=2):
```

---

## Configuration Files

eClipLint uses two configuration files:

### 1. YAML Configuration File

**Location** (in priority order):
1. `~/.ecliplint/config.yaml` (user config, highest priority)
2. `./config/config.yaml` (project config)
3. Built-in defaults (if no config file found)

**Create from example**:
```bash
# Copy example to user directory
mkdir -p ~/.ecliplint
cp config/config.example.yaml ~/.ecliplint/config.yaml

# Edit with your settings
nano ~/.ecliplint/config.yaml
```

**What it contains**:
- Local mode settings (models, prompts, generation)
- Cloud mode settings (models, selection strategy, fallbacks)
- Learning system configuration
- Hotkey definitions
- Language-specific settings
- Advanced features

### 2. Environment Variables (.env)

**Location**: `.env` in project root OR environment variables

**Create from example**:
```bash
cp .env.example .env
nano .env  # Add your OPENROUTER_API_KEY
```

**What it contains**:
- API keys (OpenRouter)
- Mode overrides
- Cost limits
- Learning system toggles
- Debug settings

**Priority**: Environment variables override YAML config

---

## Environment Variables

### Essential Variables

#### OPENROUTER_API_KEY (Required for Cloud Mode)

```bash
# In .env file
OPENROUTER_API_KEY=sk-or-v1-1234567890abcdef...

# Or export directly
export OPENROUTER_API_KEY=sk-or-v1-1234567890abcdef...
```

**Get your key**: https://openrouter.ai/keys

### Optional Variables

#### Model Selection

```bash
# Override default cloud model
ECLIPLINT_CLOUD_MODEL=anthropic/claude-4.5-sonnet:beta

# Override fallback model
ECLIPLINT_CLOUD_FALLBACK=openai/gpt-4o

# Override local model
ECLIPLINT_LOCAL_MODEL=mlx-community/Qwen2.5-Coder-7B-Instruct-4bit
```

#### Mode Selection

```bash
# Default mode (local or cloud)
ECLIPLINT_MODE=local  # Default: local
```

#### Learning System

```bash
# Enable/disable learning
ECLIPLINT_ENABLE_LEARNING=true  # Default: true (cloud mode only)

# Storage path for patterns
ECLIPLINT_LEARNING_PATH=~/.ecliplint/learned_patterns/

# Max patterns per language
ECLIPLINT_MAX_PATTERNS=1000  # Default: 1000
```

#### Cost Limits

```bash
# Warn when monthly cost exceeds this (USD)
ECLIPLINT_WARN_AT_MONTHLY_USD=10.0

# Hard limit: stop when monthly cost exceeds this (USD)
ECLIPLINT_MAX_MONTHLY_USD=50.0

# Hard limit: reject repairs costing more than this (USD)
ECLIPLINT_MAX_PER_REPAIR_USD=0.50
```

#### Debug

```bash
# Enable debug logging
ECLIPLINT_DEBUG=true

# Log file path
ECLIPLINT_LOG_FILE=~/.ecliplint/debug.log
```

---

## Cloud Mode Setup

### Step-by-Step Setup

#### 1. Get OpenRouter API Key

1. Visit https://openrouter.ai/keys
2. Sign up or log in
3. Create a new API key
4. Copy the key (starts with `sk-or-v1-...`)

#### 2. Add API Key to .env

```bash
# Create .env from example
cp .env.example .env

# Edit .env
nano .env

# Add your key
OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE
```

**Security**: Never commit `.env` to git (already in `.gitignore`)

#### 3. Enable Cloud Mode

```bash
ecliplint --enable-cloud
```

**Interactive prompt**:
```
⚠️  Cloud mode sends code to OpenRouter API
⚠️  Only use for NON-PROPRIETARY code

Enter OpenRouter API key: sk-or-v1-...

✅ Cloud mode enabled

Hotkeys:
  ⌘⇧F - Local mode (private, proprietary code)
  ⌘⇧G - Cloud mode (powerful, non-proprietary code)
```

#### 4. Verify Setup

```bash
# Check configuration
ecliplint --status

# Test cloud connection
ecliplint --test-cloud

# List available models
ecliplint --list-models
```

### Model Selection Strategies

eClipLint supports three model selection strategies:

#### 1. Complexity-Based (Default, Recommended)

Automatically selects model based on code complexity:

```yaml
# config.yaml
cloud:
  selection_strategy: complexity
```

**How it works**:
- Simple code (score < 0.3) → DeepSeek Coder V3 (cheap, $0.01/repair)
- Medium code (score 0.3-0.6) → GPT-4o (balanced, $0.03/repair)
- Complex code (score > 0.6) → Claude 4.5 Sonnet (expensive, $0.06/repair)

**Complexity factors**:
- Line count
- Number of functions/classes
- Async/await usage
- Decorators
- Nesting depth

#### 2. Manual (Fixed Model)

Always use a specific model:

```bash
# In .env
ECLIPLINT_CLOUD_MODEL=anthropic/claude-4.5-sonnet:beta
```

Or in config.yaml:
```yaml
cloud:
  selection_strategy: manual
  models:
    - id: anthropic/claude-4.5-sonnet:beta
      enabled: true
```

#### 3. Cost-Optimized

Always use cheapest model:

```yaml
cloud:
  selection_strategy: cost_optimized
  # Always uses DeepSeek Coder V3 (~$0.01/repair)
```

### Available Models

eClipLint supports all OpenRouter models. Recommended models:

| Model | Use Case | Cost (per 1M tokens) | Avg Cost/Repair |
|-------|----------|---------------------|-----------------|
| **anthropic/claude-4.5-sonnet:beta** | Complex reasoning, architecture | $3.00 / $15.00 | ~$0.06 |
| **openai/gpt-4o** | General repairs, standard fixes | $2.50 / $10.00 | ~$0.03 |
| **deepseek/deepseek-coder-v3** | Simple fixes, cost-effective | $0.27 / $1.10 | ~$0.01 |
| **qwen/qwq-32b-preview** | Reasoning, debugging | $0.12 / $0.60 | ~$0.02 |

**Get latest models**:
```bash
ecliplint --list-models
```

Models updated weekly by OpenRouter.

---

## Learning System

### What It Does

The learning system extracts patterns from successful repairs and uses them to improve future repairs.

**Privacy-safe**:
- Stores abstract patterns, NOT actual code
- Example: `def foo(x, y)` → `def IDENTIFIER(ARGS)`
- Uses SHA-256 hashing for deduplication
- Automatically excludes secrets (passwords, API keys)

### Enable Learning

Learning is **enabled by default** in cloud mode, **disabled in local mode**.

```bash
# Check learning status
ecliplint --learning-stats

# Enable/disable in .env
ECLIPLINT_ENABLE_LEARNING=true  # or false
```

### Configuration

```yaml
# config.yaml
learning:
  enabled: true

  pattern_extraction:
    enabled: true
    min_confidence: 0.75  # Only learn from high-confidence repairs

  storage:
    path: ~/.ecliplint/learned_patterns/
    max_patterns_per_language: 1000  # LRU eviction when exceeded

  privacy:
    abstract_code: true  # Store patterns, not actual code
    hash_method: sha256

    # Never learn from patterns containing these
    exclude_patterns:
      - ".*password.*"
      - ".*secret.*"
      - ".*api[_-]?key.*"
      - ".*token.*"
```

### View Learning Statistics

```bash
ecliplint --learning-stats
```

**Example output**:
```
Learning Statistics (Cloud Mode)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Repairs:        1,247
Patterns Learned:     753
Quality Improvement:  +4.2% average

By Language:
  Python:      247 patterns | 94.2% → 97.8% (+3.6%)
  JavaScript:  198 patterns | 91.5% → 95.3% (+3.8%)
  TypeScript:  156 patterns | 89.7% → 94.1% (+4.4%)

Top Learned Patterns (Python):
  1. missing_colon (127 occurrences) - "Add : after def/if/for"
  2. wrong_indentation (94 occurrences) - "Use 4 spaces, not tabs"
  3. missing_import (73 occurrences) - "Add import statement"

Storage: 8.4 MB (753 patterns)
```

### Export/Import Patterns

```bash
# Export patterns for a language
ecliplint --export-patterns python > my_python_patterns.json

# Import community patterns
ecliplint --import-patterns community_python_web.json
```

---

## Cost Management

### Setting Cost Limits

```bash
# In .env
ECLIPLINT_WARN_AT_MONTHLY_USD=10.0   # Warn at $10/month
ECLIPLINT_MAX_MONTHLY_USD=50.0       # Hard limit at $50/month
ECLIPLINT_MAX_PER_REPAIR_USD=0.50    # Reject repairs >$0.50
```

**What happens**:
- **Warning**: Notification when approaching limit (continue working)
- **Hard limit**: Repairs rejected when exceeded (error message shown)
- **Per-repair limit**: Expensive repairs rejected (fallback to cheaper model)

### View Usage

```bash
ecliplint --cloud-usage
```

**Example output**:
```
Cloud Usage (OpenRouter)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This Month (December 2024):
  Total Repairs:     147
  Total Tokens:      1,247,853
  Total Cost:        $4.23 USD

By Model:
  anthropic/claude-4.5-sonnet:beta
    Repairs:     67 (45.6%)
    Tokens:      678,453
    Cost:        $2.89 ($0.043/repair)

  openai/gpt-4o
    Repairs:     54 (36.7%)
    Tokens:      423,892
    Cost:        $1.12 ($0.021/repair)

  deepseek/deepseek-coder-v3
    Repairs:     26 (17.7%)
    Tokens:      145,508
    Cost:        $0.22 ($0.008/repair)

Cost Projection (based on usage):
  This month: ~$6.50 USD
  Annual:     ~$78.00 USD

Cost per repair: $0.029 average
```

### Cost Estimation

**Typical usage costs**:

| Usage | Repairs/Month | Avg Cost/Repair | Monthly Cost |
|-------|---------------|-----------------|--------------|
| Light | 50 | $0.03 | ~$1.50 |
| Medium | 200 | $0.03 | ~$6.00 |
| Heavy | 500 | $0.03 | ~$15.00 |

**Cost varies by model**:
- DeepSeek Coder V3: ~$0.01/repair (cheap)
- GPT-4o: ~$0.03/repair (medium)
- Claude 4.5 Sonnet: ~$0.06/repair (expensive, high quality)

**Complexity-based selection optimizes cost automatically.**

---

## Hotkey Configuration

### Two Hotkeys, Two Modes

- **⌘⇧F** (Cmd+Shift+F): Local mode (private, proprietary code)
- **⌘⇧G** (Cmd+Shift+G): Cloud mode (powerful, non-proprietary code)

### Setup (macOS Automator)

See [HOTKEY_SETUP.md](HOTKEY_SETUP.md) for detailed instructions.

**Quick setup**:

1. Open **Automator** (Applications → Automator)
2. Create **Quick Action**
3. Add **Run Shell Script**:
   - For ⌘⇧F (local): `/usr/local/bin/ecliplint --local`
   - For ⌘⇧G (cloud): `/usr/local/bin/ecliplint --cloud`
4. Save as:
   - "eClipLint Local" (for ⌘⇧F)
   - "eClipLint Cloud" (for ⌘⇧G)
5. System Settings → Keyboard → Keyboard Shortcuts → Services
6. Assign hotkeys

### Configure in YAML

```yaml
# config.yaml
hotkeys:
  local:
    key: "cmd+shift+f"
    description: "Repair code locally (100% private)"

  cloud:
    key: "cmd+shift+g"
    description: "Repair code with cloud models (powerful + learning)"
```

---

## Advanced Settings

### Parallel Processing

```yaml
# config.yaml
advanced:
  parallel:
    enabled: true
    max_workers: 4  # Number of parallel repairs
```

**Use case**: Repair multiple code segments simultaneously.

### Experimental Features

```yaml
# config.yaml
advanced:
  experimental:
    multi_file_repair: false  # Repair multiple files at once
    explain_mode: false       # Show explanation of repairs
    watch_mode: false         # Auto-repair on clipboard change
```

### Debug Logging

```yaml
# config.yaml
advanced:
  debug:
    enabled: true
    log_file: ~/.ecliplint/debug.log
    log_level: DEBUG  # DEBUG, INFO, WARNING, ERROR
```

Or via environment variable:
```bash
ECLIPLINT_DEBUG=true ecliplint
```

### Language-Specific Settings

```yaml
# config.yaml
languages:
  python:
    formatter: black
    linter: ruff
    enable_type_checking: false

  javascript:
    formatter: prettier
    linter: eslint
    enable_type_checking: false

  typescript:
    formatter: prettier
    linter: eslint
    enable_type_checking: true

  sql:
    formatter: sqlfluff
    dialect: postgres  # postgres, mysql, sqlite, etc.
```

---

## Troubleshooting

### Cloud Mode Issues

#### Error: "OpenRouter API key not found"

**Solution**:
```bash
# Check .env file
cat .env | grep OPENROUTER_API_KEY

# If missing, add it
echo "OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY" >> .env

# Or export directly
export OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY
```

#### Error: "Unauthorized" or "Invalid API key"

**Solution**:
1. Verify API key is correct: https://openrouter.ai/keys
2. Check for extra spaces in `.env`
3. Ensure key starts with `sk-or-v1-`
4. Regenerate key if compromised

#### Error: "Monthly cost limit exceeded"

**Solution**:
```bash
# Check current usage
ecliplint --cloud-usage

# Increase limit in .env
ECLIPLINT_MAX_MONTHLY_USD=100.0

# Or wait until next month (resets automatically)
```

#### Cloud mode not working

**Solution**:
```bash
# Check if enabled
ecliplint --status

# Enable if disabled
ecliplint --enable-cloud

# Test connection
ecliplint --test-cloud

# Check debug logs
tail -f ~/.ecliplint/debug.log
```

### Learning System Issues

#### Learning not working

**Solution**:
```bash
# Check if enabled
ecliplint --learning-stats

# Enable in .env
ECLIPLINT_ENABLE_LEARNING=true

# Check storage path exists
ls -la ~/.ecliplint/learned_patterns/

# Create if missing
mkdir -p ~/.ecliplint/learned_patterns/
```

#### Patterns not improving quality

**Solution**:
- Learning requires 10-20 repairs before patterns emerge
- Check confidence threshold (default: 0.75)
- View patterns: `cat ~/.ecliplint/learned_patterns/python.json`
- Increase max patterns: `ECLIPLINT_MAX_PATTERNS=2000`

### Local Mode Issues

#### Error: "Model not found"

**Solution**:
```bash
# Re-initialize (download model)
ecliplint --init

# Or specify different model
ECLIPLINT_LOCAL_MODEL=mlx-community/Qwen2.5-Coder-7B-Instruct-4bit ecliplint --init
```

#### Slow local repairs

**Solution**:
- Use smaller model: `ministral` (faster, less accurate)
- Disable streaming: `stream: false` in config.yaml
- Check available memory: `vm_stat`

### Configuration Issues

#### Config file not loading

**Solution**:
```bash
# Check config file location
ls -la ~/.ecliplint/config.yaml

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('~/.ecliplint/config.yaml'))"

# Use example as base
cp config/config.example.yaml ~/.ecliplint/config.yaml
```

#### Environment variables not loading

**Solution**:
```bash
# Check .env file exists
ls -la .env

# Source .env manually
export $(cat .env | xargs)

# Or use direnv (automatic)
echo "dotenv" > .envrc
direnv allow
```

---

## Configuration Examples

### Example 1: Privacy-First (Local Only)

```yaml
# config.yaml
general:
  default_mode: local

cloud:
  enabled: false  # Never use cloud

learning:
  enabled: false  # No learning (maximum privacy)
```

```bash
# .env
ECLIPLINT_MODE=local
ECLIPLINT_ENABLE_LEARNING=false
```

**Use case**: Corporate environments, proprietary code, maximum privacy.

### Example 2: Quality-First (Cloud Only)

```yaml
# config.yaml
general:
  default_mode: cloud

cloud:
  enabled: true
  selection_strategy: manual
  models:
    - id: anthropic/claude-4.5-sonnet:beta  # Always use best model
      enabled: true

learning:
  enabled: true
  pattern_extraction:
    min_confidence: 0.5  # Learn aggressively
```

```bash
# .env
OPENROUTER_API_KEY=sk-or-v1-...
ECLIPLINT_MODE=cloud
ECLIPLINT_CLOUD_MODEL=anthropic/claude-4.5-sonnet:beta
ECLIPLINT_MAX_MONTHLY_USD=100.0  # Higher limit
```

**Use case**: Open-source projects, learning examples, maximum quality.

### Example 3: Cost-Optimized

```yaml
# config.yaml
cloud:
  enabled: true
  selection_strategy: cost_optimized
  models:
    - id: deepseek/deepseek-coder-v3  # Always use cheapest
      enabled: true

  cost_limits:
    warn_at_monthly_usd: 5.0
    max_monthly_usd: 10.0
    max_per_repair_usd: 0.05
```

```bash
# .env
OPENROUTER_API_KEY=sk-or-v1-...
ECLIPLINT_CLOUD_MODEL=deepseek/deepseek-coder-v3
ECLIPLINT_WARN_AT_MONTHLY_USD=5.0
ECLIPLINT_MAX_MONTHLY_USD=10.0
```

**Use case**: Budget-conscious users, high-volume usage.

### Example 4: Balanced (Complexity-Based)

```yaml
# config.yaml (default)
general:
  default_mode: local  # Local by default

cloud:
  enabled: true
  selection_strategy: complexity  # Auto-select model

  models:
    - id: anthropic/claude-4.5-sonnet:beta
      complexity_min: 0.6

    - id: openai/gpt-4o
      complexity_min: 0.4

    - id: deepseek/deepseek-coder-v3
      complexity_min: 0.0

learning:
  enabled: true
  pattern_extraction:
    min_confidence: 0.75  # Only high-confidence patterns
```

```bash
# .env
OPENROUTER_API_KEY=sk-or-v1-...
ECLIPLINT_MODE=local  # Default to local, use cloud intentionally
ECLIPLINT_WARN_AT_MONTHLY_USD=10.0
ECLIPLINT_MAX_MONTHLY_USD=25.0
```

**Use case**: Most users, balance of privacy/quality/cost.

---

## Summary

### Configuration Hierarchy

1. **Command-line flags** (highest priority)
   - `--cloud`, `--local`, `--model`, etc.

2. **Environment variables**
   - `.env` file or exported variables

3. **User config file**
   - `~/.ecliplint/config.yaml`

4. **Project config file**
   - `./config/config.yaml`

5. **Built-in defaults** (lowest priority)

### Essential Files

- `~/.ecliplint/config.yaml` - User configuration
- `.env` - API keys and overrides
- `~/.ecliplint/learned_patterns/` - Learned patterns storage
- `~/.ecliplint/usage.jsonl` - Usage tracking
- `~/.ecliplint/debug.log` - Debug logs

### Quick Commands

```bash
# Status
ecliplint --status              # Show current configuration
ecliplint --cloud-usage         # Show cloud usage and costs
ecliplint --learning-stats      # Show learning statistics

# Setup
ecliplint --init                # Initialize local mode
ecliplint --enable-cloud        # Enable cloud mode
ecliplint --test-cloud          # Test cloud connection

# Models
ecliplint --list-models         # List available OpenRouter models

# Learning
ecliplint --export-patterns python > patterns.json
ecliplint --import-patterns patterns.json

# Debug
ECLIPLINT_DEBUG=true ecliplint  # Enable debug logging
```

### Support

- **Documentation**: https://github.com/deesatzed/eClipLint
- **Issues**: https://github.com/deesatzed/eClipLint/issues
- **OpenRouter Docs**: https://openrouter.ai/docs
