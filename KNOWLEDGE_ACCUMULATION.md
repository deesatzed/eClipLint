# Knowledge Accumulation System

## Problem Statement

**Current limitation**: Agents use static knowledge from JSON files. They don't learn from:
- Successful repairs (what worked)
- Failed repairs (what didn't work)
- User-specific patterns (what code users commonly break)

**Goal**: Automatically accumulate instructional knowledge from prior fixes without storing specific user code.

---

## Design Principles

### ✅ What to Store (Instructional)
- **Pattern**: "Missing colon after function definition"
- **Fix strategy**: "Add `:` after `def function_name(args)`"
- **Context**: "Python, IndentationError"
- **Frequency**: How often this pattern occurs

### ❌ What NOT to Store (Privacy)
- Actual user code (e.g., `def process_payment(amount):`)
- Variable names (e.g., `user_email`, `api_key`)
- Comments or strings (may contain sensitive data)

**Core principle**: Store **generalizable patterns**, not **specific code**.

---

## Architecture

### File Structure

```
~/.ecliplint/
├── knowledge_cache/
│   ├── python_accumulated.json     # Auto-learned patterns
│   ├── javascript_accumulated.json
│   ├── bash_accumulated.json
│   └── ...
└── metrics.jsonl                    # Repair logs (for analysis)
```

**Static knowledge** (shipped with app):
```
knowledge/python.json  → Base knowledge (manual, curated)
```

**Accumulated knowledge** (learned from user):
```
~/.ecliplint/knowledge_cache/python_accumulated.json  → Learned patterns
```

**Combined at runtime**:
```python
# Agent loads both and merges
base_knowledge = load("knowledge/python.json")
accumulated = load("~/.ecliplint/knowledge_cache/python_accumulated.json")
merged_knowledge = merge(base_knowledge, accumulated)
```

---

## Knowledge Accumulation Format

### Structure of `python_accumulated.json`

```json
{
  "learned_patterns": [
    {
      "pattern_id": "missing_colon_def",
      "pattern_type": "SyntaxError",
      "description": "Missing colon after function definition",
      "abstract_example": {
        "broken_pattern": "def FUNCTION_NAME(ARGS)\n    BODY",
        "fixed_pattern": "def FUNCTION_NAME(ARGS):\n    BODY"
      },
      "fix_instruction": "Add `:` after closing parenthesis in function definition",
      "frequency": 47,
      "success_rate": 0.96,
      "first_seen": "2024-12-01T10:30:00Z",
      "last_seen": "2024-12-13T14:22:00Z",
      "language": "python",
      "related_errors": ["IndentationError", "SyntaxError"]
    },
    {
      "pattern_id": "unquoted_string_concat",
      "pattern_type": "TypeError",
      "description": "String concatenation with non-string type",
      "abstract_example": {
        "broken_pattern": "VARIABLE + STRING",
        "fixed_pattern": "str(VARIABLE) + STRING"
      },
      "fix_instruction": "Wrap non-string variable in str() before concatenation",
      "frequency": 23,
      "success_rate": 0.91,
      "first_seen": "2024-12-05T09:15:00Z",
      "last_seen": "2024-12-12T16:45:00Z",
      "language": "python",
      "related_errors": ["TypeError"]
    }
  ],
  "total_repairs": 1247,
  "successful_repairs": 1189,
  "overall_success_rate": 0.953,
  "last_updated": "2024-12-13T14:22:00Z"
}
```

---

## Code Abstraction Process

### How to Extract Patterns Without Storing Actual Code

**Step 1: Detect repair type**
```python
def classify_repair(broken: str, fixed: str) -> dict:
    """Classify what kind of repair was performed."""
    diff = difflib.unified_diff(broken.splitlines(), fixed.splitlines())
    changes = [line for line in diff if line.startswith('+') or line.startswith('-')]

    # Analyze changes
    if any(':' in line for line in changes):
        return {"type": "missing_colon"}
    if any('import ' in line for line in changes):
        return {"type": "missing_import"}
    if re.search(r'\s{4,}', fixed) and not re.search(r'\s{4,}', broken):
        return {"type": "indentation"}
    # ... more patterns
```

**Step 2: Abstract the code**
```python
def abstract_code(code: str, language: str) -> str:
    """
    Replace specific code with generic placeholders.

    Examples:
      def process_payment(amount): → def FUNCTION_NAME(ARGS):
      user_email = "test@example.com" → VARIABLE = STRING
      for i in range(10): → for VARIABLE in ITERABLE:
    """
    # Tokenize code
    tokens = tokenize(code, language)

    # Replace with placeholders
    abstract = []
    for token in tokens:
        if token.type == "IDENTIFIER":
            abstract.append("VARIABLE" if is_variable(token) else "FUNCTION_NAME")
        elif token.type == "STRING":
            abstract.append("STRING")
        elif token.type == "NUMBER":
            abstract.append("NUMBER")
        else:
            abstract.append(token.value)  # Keep keywords, operators

    return "".join(abstract)
```

**Step 3: Extract instruction**
```python
def extract_instruction(pattern_type: str, broken: str, fixed: str) -> str:
    """Generate human-readable instruction."""
    instructions = {
        "missing_colon": "Add `:` after closing parenthesis",
        "missing_import": "Add missing import statement at top of file",
        "indentation": "Fix indentation to use 4 spaces per level",
        # ...
    }
    return instructions.get(pattern_type, "Fix syntax error")
```

**Example**:

**Input** (actual user code):
```python
# Broken
def calculate_total(items):
return sum(item.price for item in items)

# Fixed
def calculate_total(items):
    return sum(item.price for item in items)
```

**Abstracted pattern** (stored):
```json
{
  "pattern_type": "indentation",
  "abstract_example": {
    "broken_pattern": "def FUNCTION_NAME(ARGS):\nreturn EXPRESSION",
    "fixed_pattern": "def FUNCTION_NAME(ARGS):\n    return EXPRESSION"
  },
  "fix_instruction": "Add 4-space indentation after function definition"
}
```

**No sensitive data stored!**

---

## Implementation

### 1. Update `base_agent.py` to Log Repairs

```python
# python/clipfix/engines/agents/base_agent.py

from pathlib import Path
import json
from datetime import datetime
from typing import Optional

class BaseAgent(ABC):
    # ... existing code ...

    def repair(self, code: str) -> str:
        """Repair code and log the result for learning."""
        # Existing repair logic
        repaired = self._generate_repair(code)

        # Log successful repair for learning
        if self._is_valid_repair(code, repaired):
            self._log_repair_for_learning(code, repaired)

        return repaired

    def _log_repair_for_learning(self, broken: str, fixed: str):
        """Log repair pattern for knowledge accumulation."""
        # Extract abstract pattern (no actual code stored)
        pattern = self._extract_pattern(broken, fixed)

        if pattern:
            self._append_to_accumulated_knowledge(pattern)

    def _extract_pattern(self, broken: str, fixed: str) -> Optional[dict]:
        """
        Extract abstract pattern from broken/fixed code pair.

        Returns pattern dict or None if not generalizable.
        """
        # Classify repair type
        repair_type = self._classify_repair(broken, fixed)

        if not repair_type:
            return None

        # Abstract code (remove specifics)
        abstract_broken = self._abstract_code(broken)
        abstract_fixed = self._abstract_code(fixed)

        # Generate instruction
        instruction = self._generate_instruction(repair_type, broken, fixed)

        return {
            "pattern_type": repair_type,
            "abstract_example": {
                "broken_pattern": abstract_broken,
                "fixed_pattern": abstract_fixed
            },
            "fix_instruction": instruction,
            "timestamp": datetime.now().isoformat(),
            "language": self.language
        }

    def _classify_repair(self, broken: str, fixed: str) -> Optional[str]:
        """Classify what type of repair was performed."""
        import difflib

        diff_lines = list(difflib.unified_diff(
            broken.splitlines(),
            fixed.splitlines(),
            lineterm=""
        ))

        changes = [l for l in diff_lines if l.startswith('+') or l.startswith('-')]

        # Detect pattern types
        if any(':' in l for l in changes):
            return "missing_colon"

        if any('import ' in l for l in changes):
            return "missing_import"

        if self._indentation_changed(broken, fixed):
            return "indentation"

        if any('"' in l or "'" in l for l in changes):
            return "quote_style"

        # ... more pattern detection

        return None

    def _abstract_code(self, code: str) -> str:
        """Replace specific code with generic placeholders."""
        # Simple abstraction (can be improved with AST parsing)
        import re

        abstract = code

        # Replace string literals
        abstract = re.sub(r'"[^"]*"', 'STRING', abstract)
        abstract = re.sub(r"'[^']*'", 'STRING', abstract)

        # Replace numbers
        abstract = re.sub(r'\b\d+\b', 'NUMBER', abstract)

        # Replace identifiers (but keep keywords)
        keywords = {'def', 'class', 'if', 'for', 'while', 'import', 'from', 'return'}
        words = re.findall(r'\b[a-zA-Z_]\w*\b', abstract)
        for word in set(words):
            if word not in keywords:
                abstract = re.sub(r'\b' + word + r'\b', 'IDENTIFIER', abstract)

        return abstract

    def _generate_instruction(self, pattern_type: str, broken: str, fixed: str) -> str:
        """Generate human-readable fix instruction."""
        instructions = {
            "missing_colon": "Add `:` after function/class/if/for/while definition",
            "missing_import": "Add missing import statement",
            "indentation": "Fix indentation to use 4 spaces per level",
            "quote_style": "Normalize quote style (use single quotes)",
        }
        return instructions.get(pattern_type, "Fix syntax error")

    def _append_to_accumulated_knowledge(self, pattern: dict):
        """Append pattern to accumulated knowledge file."""
        cache_dir = Path.home() / ".ecliplint" / "knowledge_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        cache_file = cache_dir / f"{self.language}_accumulated.json"

        # Load existing
        if cache_file.exists():
            accumulated = json.loads(cache_file.read_text())
        else:
            accumulated = {
                "learned_patterns": [],
                "total_repairs": 0,
                "successful_repairs": 0,
                "last_updated": None
            }

        # Check if pattern already exists (update frequency)
        existing = None
        for p in accumulated["learned_patterns"]:
            if p.get("pattern_type") == pattern["pattern_type"]:
                existing = p
                break

        if existing:
            # Increment frequency
            existing["frequency"] = existing.get("frequency", 1) + 1
            existing["last_seen"] = pattern["timestamp"]
        else:
            # Add new pattern
            pattern["frequency"] = 1
            pattern["first_seen"] = pattern["timestamp"]
            pattern["last_seen"] = pattern["timestamp"]
            accumulated["learned_patterns"].append(pattern)

        # Update stats
        accumulated["total_repairs"] = accumulated.get("total_repairs", 0) + 1
        accumulated["successful_repairs"] = accumulated.get("successful_repairs", 0) + 1
        accumulated["last_updated"] = pattern["timestamp"]

        # Save
        cache_file.write_text(json.dumps(accumulated, indent=2))
```

### 2. Update Agent Prompts to Include Accumulated Knowledge

```python
# In base_agent.py

def _load_knowledge(self) -> dict:
    """Load both static and accumulated knowledge."""
    # Load base knowledge (static, shipped with app)
    base_knowledge = self._load_base_knowledge()

    # Load accumulated knowledge (learned from user)
    accumulated_knowledge = self._load_accumulated_knowledge()

    # Merge
    return self._merge_knowledge(base_knowledge, accumulated_knowledge)

def _load_accumulated_knowledge(self) -> dict:
    """Load accumulated knowledge from user's cache."""
    cache_file = Path.home() / ".ecliplint" / "knowledge_cache" / f"{self.language}_accumulated.json"

    if not cache_file.exists():
        return {"learned_patterns": []}

    try:
        return json.loads(cache_file.read_text())
    except Exception:
        return {"learned_patterns": []}

def _merge_knowledge(self, base: dict, accumulated: dict) -> dict:
    """Merge base and accumulated knowledge."""
    merged = base.copy()

    # Add accumulated patterns to prompt
    if accumulated.get("learned_patterns"):
        # Build instructional text from patterns
        learned_instructions = self._format_learned_patterns(
            accumulated["learned_patterns"]
        )

        # Append to repair prompt
        merged["repair_prompt"] = (
            base.get("repair_prompt", "") +
            "\n\n## Recently Learned Patterns (Your Common Errors)\n\n" +
            learned_instructions
        )

    return merged

def _format_learned_patterns(self, patterns: list) -> str:
    """Format learned patterns as instructional text for prompt."""
    # Sort by frequency (most common first)
    sorted_patterns = sorted(
        patterns,
        key=lambda p: p.get("frequency", 0),
        reverse=True
    )

    # Take top 10 most frequent
    top_patterns = sorted_patterns[:10]

    instructions = []
    for i, pattern in enumerate(top_patterns, 1):
        freq = pattern.get("frequency", 1)
        instruction = pattern.get("fix_instruction", "")
        example = pattern.get("abstract_example", {})

        instructions.append(
            f"{i}. **{instruction}** (seen {freq}x)\n"
            f"   - Broken: `{example.get('broken_pattern', '')}`\n"
            f"   - Fixed: `{example.get('fixed_pattern', '')}`"
        )

    return "\n".join(instructions)
```

---

## Example: How It Works

### Scenario 1: First Repair

**User code**:
```python
def calculate_total(items)
    return sum(item.price for item in items)
```

**Agent**:
1. Detects missing colon
2. Repairs: `def calculate_total(items):`
3. Extracts pattern: `{"pattern_type": "missing_colon", "frequency": 1, ...}`
4. Saves to `~/.ecliplint/knowledge_cache/python_accumulated.json`

**Accumulated knowledge** (after 1 repair):
```json
{
  "learned_patterns": [
    {
      "pattern_type": "missing_colon",
      "abstract_example": {
        "broken_pattern": "def IDENTIFIER(IDENTIFIER)\n    return EXPRESSION",
        "fixed_pattern": "def IDENTIFIER(IDENTIFIER):\n    return EXPRESSION"
      },
      "fix_instruction": "Add `:` after function definition",
      "frequency": 1
    }
  ]
}
```

### Scenario 2: Pattern Repeats (10th Repair)

**User makes same mistake again**:
```python
def process_order(order)
    order.status = 'complete'
```

**Agent**:
1. Detects missing colon (again)
2. Repairs it
3. Updates frequency: `"frequency": 10`

**Prompt now includes** (automatically):
```
## Recently Learned Patterns (Your Common Errors)

1. **Add `:` after function definition** (seen 10x)
   - Broken: `def IDENTIFIER(IDENTIFIER)\n    BODY`
   - Fixed: `def IDENTIFIER(IDENTIFIER):\n    BODY`
```

**Result**: AI becomes **more likely** to fix this specific error (it's emphasized in the prompt).

---

## Privacy & Security

### What Gets Stored

✅ **Safe to store**:
- Abstract patterns (`def IDENTIFIER(ARGS):`)
- Fix instructions ("Add `:` after function definition")
- Error types (IndentationError, SyntaxError)
- Frequencies (how often pattern occurs)
- Timestamps

❌ **Never stored**:
- Actual variable names (`calculate_total`, `user_email`)
- String literals (`"password123"`, `"api_key"`)
- Comments (`# TODO: fix security bug`)
- Function bodies (actual logic)

### Opt-Out

Add flag to disable learning:
```bash
ecliplint --no-learning  # Don't accumulate knowledge
```

Or global config:
```yaml
# ~/.ecliplint/config.yaml
learning:
  enabled: false  # Disable knowledge accumulation
```

---

## Benefits

### 1. Personalized Repair Quality

**Before** (static knowledge):
- Agent knows 4 common Python errors (from `knowledge/python.json`)

**After** (accumulated knowledge):
- Agent knows 4 common errors + **your specific patterns**
- If you frequently forget colons, agent prioritizes that fix
- If you mix tabs/spaces, agent learns your indentation style

### 2. Community Knowledge Sharing (Future)

```bash
# Export your learned patterns
ecliplint --export-knowledge > my_patterns.json

# Import community patterns
ecliplint --import-knowledge community_patterns.json
```

**Community repository**:
```
github.com/deesatzed/eClipLint-knowledge/
├── python/
│   ├── web_frameworks.json    (Django, Flask common errors)
│   ├── data_science.json      (NumPy, Pandas patterns)
│   └── beginner_patterns.json (Common beginner mistakes)
├── javascript/
│   ├── react.json             (React common errors)
│   └── node.json              (Node.js patterns)
```

### 3. Continuous Improvement

**Week 1**: Agent fixes 94.2% of repairs
**Week 4**: Agent fixes 97.8% (learned from 150 successful repairs)
**Week 8**: Agent fixes 99.1% (knows your specific coding patterns)

---

## Implementation Plan

### Phase 1: Basic Pattern Extraction (Week 1)
- [ ] Add `_extract_pattern()` to `base_agent.py`
- [ ] Implement simple abstraction (regex-based)
- [ ] Save to `~/.ecliplint/knowledge_cache/`

### Phase 2: Pattern Integration (Week 2)
- [ ] Load accumulated knowledge in `_load_knowledge()`
- [ ] Merge with base knowledge
- [ ] Format as instructional text for prompt

### Phase 3: Testing & Refinement (Week 3)
- [ ] Test privacy (verify no code leaks)
- [ ] Test learning effectiveness (does quality improve?)
- [ ] Add opt-out flag (`--no-learning`)

### Phase 4: Advanced Features (Month 2)
- [ ] AST-based abstraction (better than regex)
- [ ] Pattern similarity detection (group related patterns)
- [ ] Export/import for community sharing
- [ ] Dashboard showing learned patterns

---

## Monitoring

### View Learned Patterns

```bash
# Show accumulated knowledge
cat ~/.ecliplint/knowledge_cache/python_accumulated.json | jq '.learned_patterns'

# Top 10 most frequent patterns
cat ~/.ecliplint/knowledge_cache/python_accumulated.json | \
  jq '.learned_patterns | sort_by(.frequency) | reverse | .[0:10] | .[] | {type: .pattern_type, freq: .frequency, instruction: .fix_instruction}'
```

### Dashboard (Future)

```
┌────────────────────────────────────────────────────────────┐
│ eClipLint Learning Dashboard                               │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Total Repairs: 1,247                                      │
│  Learned Patterns: 23                                      │
│  Success Rate: 95.3% → 97.8% (+2.5% from learning)         │
│                                                             │
│  Top Patterns:                                             │
│  1. Missing colon (47x) - "Add : after function def"       │
│  2. Indentation (34x) - "Use 4 spaces per level"           │
│  3. Missing import (23x) - "Add import at top"             │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

---

## Summary

**Answer**: **NO**, agents currently don't have accumulated knowledge.

**Solution**: Implement knowledge accumulation system that:
- ✅ Extracts **abstract patterns** from successful repairs
- ✅ Stores **instructional fixes** (not actual code)
- ✅ **Merges** accumulated knowledge with base prompts
- ✅ **Privacy-safe** (no user code stored)
- ✅ **Personalized** (learns your specific error patterns)
- ✅ **Community-shareable** (export/import patterns)

**Impact**: Agent quality improves over time based on **your** coding patterns.
