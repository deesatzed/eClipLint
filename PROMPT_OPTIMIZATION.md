# Prompt Optimization & Measurement Strategy

## Problem Statement

**How do we know if we optimized each prompt?**

We need objective, measurable criteria to evaluate prompt quality and track improvements over time.

---

## Success Metrics

### 1. **Formatter Pass Rate** (Primary Metric)

**Definition**: Percentage of repaired code that successfully passes the deterministic formatter.

**Measurement**:
```python
formatter_pass_rate = (successful_formats_after_repair / total_repairs) * 100
```

**Target**: >95% (repaired code should almost always format cleanly)

**Why this matters**: If repaired code still fails formatting, the AI didn't truly fix the syntax.

**Implementation**:
```python
# In llm.py or agents/base_agent.py
import json
from pathlib import Path
from datetime import datetime

METRICS_FILE = Path.home() / ".ecliplint_metrics.jsonl"

def log_repair_attempt(language: str, success: bool, code_before: str, code_after: str):
    """Log each repair attempt for later analysis."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "language": language,
        "success": success,  # Did formatter pass after repair?
        "code_length": len(code_before),
        "changes": len(code_after) - len(code_before),
    }
    with METRICS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
```

**Analysis script**:
```bash
# Show formatter pass rate per language
cat ~/.ecliplint_metrics.jsonl | jq -r '[.language, .success] | @csv' | \
  awk -F, '{lang[$1]++; if($2=="true") pass[$1]++}
           END {for(l in lang) printf "%s: %.1f%% (%d/%d)\n", l, 100*pass[l]/lang[l], pass[l], lang[l]}'

# Output:
# python: 94.2% (162/172)
# javascript: 97.3% (143/147)
# bash: 89.1% (49/55)
```

---

### 2. **Syntax Validity** (Secondary Metric)

**Definition**: Percentage of repaired code that is syntactically valid (parseable).

**Measurement**:
```python
def is_valid_python(code: str) -> bool:
    try:
        compile(code, "<string>", "exec")
        return True
    except SyntaxError:
        return False

def is_valid_javascript(code: str) -> bool:
    proc = subprocess.run(
        ["node", "--check"],
        input=code,
        capture_output=True,
        text=True
    )
    return proc.returncode == 0

def is_valid_bash(code: str) -> bool:
    proc = subprocess.run(
        ["bash", "-n"],  # -n: syntax check only
        input=code,
        capture_output=True,
        text=True
    )
    return proc.returncode == 0
```

**Target**: 100% (all repaired code must be syntactically valid)

---

### 3. **Test Case Pass Rate** (Validation Metric)

**Definition**: Percentage of test_cases in knowledge/*.json that pass.

**Measurement**:
```python
# pytest tests/test_prompt_quality.py
import json
from pathlib import Path
from clipfix.engines.agents.manager import ManagerAgent
from clipfix.engines.llm import _load_model
from clipfix.engines.detect_and_format import _format_code

def test_python_prompt_quality():
    """Test Python agent against all test_cases in knowledge/python.json."""
    model, tokenizer = _load_model()
    manager = ManagerAgent(model, tokenizer)

    knowledge = json.loads(Path("knowledge/python.json").read_text())

    passed = 0
    total = len(knowledge["test_cases"])

    for i, test_case in enumerate(knowledge["test_cases"]):
        repaired = manager.repair(test_case["broken"], "python")

        # Check if repaired code passes formatter
        try:
            formatted = _format_code("python", repaired)
            passed += 1
        except Exception as e:
            print(f"Test case {i+1} failed: {e}")
            print(f"  Broken:   {test_case['broken']!r}")
            print(f"  Repaired: {repaired!r}")

    pass_rate = (passed / total) * 100
    print(f"\nPython prompt quality: {pass_rate:.1f}% ({passed}/{total})")

    assert pass_rate >= 90, f"Prompt quality below threshold: {pass_rate}%"
```

**Target**: 100% of test_cases should pass

---

### 4. **Change Minimality** (Quality Metric)

**Definition**: Repaired code should have minimal changes (don't over-refactor).

**Measurement**:
```python
import difflib

def calculate_change_ratio(before: str, after: str) -> float:
    """Calculate ratio of changed lines."""
    before_lines = before.splitlines()
    after_lines = after.splitlines()

    diff = list(difflib.unified_diff(before_lines, after_lines, lineterm=""))
    changed_lines = len([l for l in diff if l.startswith("+") or l.startswith("-")])
    total_lines = max(len(before_lines), len(after_lines))

    return changed_lines / total_lines if total_lines > 0 else 0

# Log in metrics
entry["change_ratio"] = calculate_change_ratio(code_before, code_after)
```

**Target**: <30% (most code should be preserved)

**Why this matters**: If AI changes 80% of code, it's likely over-refactoring (changing logic).

---

### 5. **Repair Time** (Performance Metric)

**Definition**: Time taken to repair code.

**Measurement**:
```python
import time

start = time.time()
repaired = manager.repair(code, language)
duration = time.time() - start

entry["repair_time_ms"] = int(duration * 1000)
```

**Target**: <5 seconds per repair (user patience threshold)

---

## Prompt Optimization Workflow

### Step 1: Establish Baseline

```bash
# Run all test cases against current prompts
pytest tests/test_prompt_quality.py -v

# Output:
# test_python_prompt_quality ... PASSED (94.2% pass rate)
# test_javascript_prompt_quality ... PASSED (97.3% pass rate)
# test_bash_prompt_quality ... FAILED (89.1% pass rate)
```

### Step 2: Identify Weaknesses

```bash
# Analyze metrics for Bash (lowest pass rate)
cat ~/.ecliplint_metrics.jsonl | jq 'select(.language == "bash" and .success == false)'

# Output shows common failure patterns:
# - Missing quotes around variables
# - Incorrect [[ ]] usage
# - Missing semicolons
```

### Step 3: Improve Prompt

Edit `knowledge/bash.json`:

```diff
  "repair_prompt": "You are an expert in Bash scripting and shell best practices.

+ ## CRITICAL: Variable Quoting
+
+ ALWAYS quote variables to prevent word splitting:
+ - Correct: echo \"$var\"
+ - Incorrect: echo $var
+
+ This is the #1 most common error. Check EVERY variable reference.
+
  ## Common Syntax Errors to Fix

  1. **Missing spaces in conditionals**: Spaces required around `[` and `]`
```

### Step 4: Re-test

```bash
pytest tests/test_prompt_quality.py::test_bash_prompt_quality

# Output:
# test_bash_prompt_quality ... PASSED (96.4% pass rate)  # ✓ Improved!
```

### Step 5: A/B Test (Optional)

```python
# Test two prompt versions side-by-side
prompt_v1 = load_prompt("knowledge/bash.json")
prompt_v2 = load_prompt("knowledge/bash_v2.json")  # Experimental

results_v1 = test_prompt(prompt_v1, test_cases)
results_v2 = test_prompt(prompt_v2, test_cases)

print(f"V1 pass rate: {results_v1.pass_rate}%")
print(f"V2 pass rate: {results_v2.pass_rate}%")

# Choose winner, deploy
```

### Step 6: Continuous Monitoring

```bash
# Weekly report: Email metrics summary
python scripts/generate_metrics_report.py

# Output:
# Week of 2024-12-09:
# - Total repairs: 1,247
# - Overall formatter pass rate: 95.3% (↑ 1.2% from last week)
# - Python: 97.1%
# - JavaScript: 98.2%
# - Bash: 91.4% (⚠ below target, needs improvement)
```

---

## Automated Prompt Optimization (Future)

### Concept: Genetic Algorithm for Prompts

```python
# 1. Start with base prompt
base_prompt = load_prompt("knowledge/python.json")

# 2. Generate variations
variations = [
    base_prompt + "\n## CRITICAL: Always use 4 spaces for indentation",
    base_prompt + "\n## PRIORITY: Fix IndentationError first",
    # ... 10 variations
]

# 3. Test each variation
results = {}
for i, prompt in enumerate(variations):
    pass_rate = test_prompt_against_all_cases(prompt, test_cases)
    results[i] = pass_rate

# 4. Keep best performers
best_prompts = sorted(results.items(), key=lambda x: x[1], reverse=True)[:3]

# 5. Combine best elements (genetic crossover)
next_generation = combine_prompts(best_prompts)

# 6. Repeat for N generations
# 7. Deploy winner
```

**Challenges**:
- Prompt changes are discrete (not continuous optimization)
- Hard to define "crossover" for text prompts
- Risk of overfitting to test_cases

**Better approach**: Manual iteration based on metrics + user feedback.

---

## Metrics Dashboard (Future Enhancement)

Create web dashboard to visualize metrics:

```
┌────────────────────────────────────────────────────────────┐
│ eClipLint Prompt Quality Dashboard                         │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Overall Formatter Pass Rate: 95.3% ▲ 1.2%                │
│  ████████████████████████░░ 95.3%                          │
│                                                             │
│  By Language:                                              │
│  ┌─────────────┬──────────┬────────┬──────────┐           │
│  │ Language    │ Pass Rate│ Repairs│ Avg Time │           │
│  ├─────────────┼──────────┼────────┼──────────┤           │
│  │ JavaScript  │ 98.2% ✓  │  1,142 │   2.3s   │           │
│  │ Python      │ 97.1% ✓  │  3,421 │   2.8s   │           │
│  │ Bash        │ 91.4% ⚠  │    284 │   3.1s   │           │
│  │ SQL         │ 93.7% ✓  │    156 │   2.1s   │           │
│  │ Rust        │ 95.8% ✓  │     89 │   2.9s   │           │
│  └─────────────┴──────────┴────────┴──────────┘           │
│                                                             │
│  Recent Failures (click to investigate):                   │
│  • Bash: Unquoted variable in conditional (3 occurrences)  │
│  • Python: Missing colon after function def (2 occurrences)│
│                                                             │
│  Prompt Improvement Suggestions:                           │
│  📝 Bash: Emphasize variable quoting rules                 │
│  📝 Python: Add more examples with function definitions    │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

**Implementation**:
- Python backend: Flask/FastAPI serving metrics from JSONL
- Frontend: HTML/JavaScript with charts (Chart.js)
- Update frequency: Real-time (WebSocket) or polling

---

## Implementation Plan

### Phase 1: Basic Metrics (Week 1)
- [ ] Add `log_repair_attempt()` to `base_agent.py`
- [ ] Create `~/.ecliplint_metrics.jsonl`
- [ ] Log: timestamp, language, success, code_length, repair_time

### Phase 2: Test Suite (Week 2)
- [ ] Create `tests/test_prompt_quality.py`
- [ ] Implement tests for all 7 languages
- [ ] CI/CD integration (GitHub Actions)

### Phase 3: Analysis Tools (Week 3)
- [ ] Create `scripts/analyze_metrics.py`
- [ ] Generate weekly reports
- [ ] Identify low-performing prompts

### Phase 4: Continuous Improvement (Ongoing)
- [ ] Monthly prompt reviews based on metrics
- [ ] Community contributions (GitHub Issues for failed repairs)
- [ ] A/B testing for major prompt changes

---

## Example: Optimizing Python Prompt

**Baseline metrics** (week 1):
```
Python formatter pass rate: 94.2% (162/172 repairs)
Average repair time: 2.8s
Change ratio: 28.3%
```

**Analysis**: 10 failures due to:
- 4x: Missing colons after function definitions
- 3x: Incorrect indentation (mixed tabs/spaces)
- 2x: Missing imports
- 1x: Over-refactoring (renamed variables)

**Prompt changes**:
```diff
+ ## CRITICAL PRIORITIES (Fix in this order)
+
+ 1. **Colons**: Add `:` after EVERY if/for/while/def/class/try/except/with
+ 2. **Indentation**: Use EXACTLY 4 spaces (never tabs, never 2 spaces)
+ 3. **Imports**: Add missing imports ONLY if obvious (sys, os, re, etc.)
+
+ ## NEVER DO
+
+ - Do NOT rename variables (preserve original names)
+ - Do NOT change logic (only fix syntax)
+ - Do NOT add comments (output code only)
```

**New metrics** (week 2):
```
Python formatter pass rate: 97.8% (169/173 repairs)  # ✓ +3.6%
Average repair time: 2.7s  # ✓ Slightly faster
Change ratio: 24.1%  # ✓ More minimal
```

**Conclusion**: Prompt improved by emphasizing priorities and adding "NEVER DO" rules.

---

## Key Takeaways

1. **Metrics-driven optimization**: Use data, not intuition
2. **Test cases are gold**: Add every failure to test suite
3. **Iterate weekly**: Small improvements compound
4. **Monitor continuously**: Catch regressions early
5. **Community feedback**: Users find edge cases you miss

**Target**: All languages >95% formatter pass rate by v1.1 release.
