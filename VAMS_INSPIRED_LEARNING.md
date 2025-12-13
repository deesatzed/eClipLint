# VAMS-Inspired Knowledge Accumulation for eClipLint

## Research Source

**VAMS (Vector-Attractor Memory System)**: `/Volumes/WS4TB/vamswsbu1112/VAMS_WORKSPACE/core/vams`

Analyzed files:
- `adaptive_agent.py` - Confidence-based adaptive behavior
- `incremental_cache.py` - Multi-strategy file change detection
- `skill_cache.py` - SHA-256 hash-based change tracking
- `knowledge_types.py` - Categorized learning with metrics
- `README.md` - Overall VAMS architecture

## Core VAMS Techniques Applied to eClipLint

### 1. Hash-Based Change Detection (from `skill_cache.py`)

**VAMS Pattern**:
```python
class SkillHashRegistry:
    def compute_hash(content: str) -> str:
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def has_changed(skill_id: str, content: str) -> bool:
        new_hash = self.compute_hash(content)
        cached = self._hashes.get(skill_id)
        return cached is None or cached.content_hash != new_hash
```

**eClipLint Application**:
- Detect if we've already seen a repair pattern
- Avoid storing duplicate patterns
- Track pattern frequency efficiently
- Use SHA-256 for pattern identity

**Implementation**:
```python
# python/clipfix/engines/pattern_learner.py

class PatternHash:
    """SHA-256-based pattern deduplication (VAMS-inspired)."""

    @staticmethod
    def compute_pattern_hash(broken: str, fixed: str, language: str) -> str:
        """Compute unique hash for a repair pattern."""
        combined = f"{language}:{broken}:{fixed}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()

    def is_duplicate(self, pattern_hash: str) -> bool:
        """Check if pattern already learned."""
        return pattern_hash in self._pattern_registry
```

---

### 2. Incremental Caching (from `incremental_cache.py`)

**VAMS Pattern**:
```python
class IncrementalCache:
    """Multi-strategy cache invalidation."""

    def has_file_changed(file_path: Path) -> bool:
        # Strategy 1: mtime (fast)
        if stat.st_mtime != cached.mtime:
            return True

        # Strategy 2: size (fast)
        if stat.st_size != cached.size:
            return True

        # Strategy 3: content hash (accurate)
        # Only if above pass
        return False

    def _evict_if_needed(self):
        """LRU eviction when over capacity."""
        while len(self._file_metadata) > self.max_cache_size:
            oldest_key = next(iter(self._file_metadata))
            self._file_metadata.pop(oldest_key, None)
```

**eClipLint Application**:
- LRU eviction for bounded pattern storage
- Periodic saves (every 50 operations)
- Multi-level change detection
- Git-aware invalidation (detect branch switches)

**Implementation**:
```python
# python/clipfix/engines/knowledge_accumulator.py

from collections import OrderedDict

class KnowledgeAccumulator:
    """VAMS-style incremental knowledge accumulation."""

    def __init__(self, cache_dir: Path, max_patterns: int = 1000):
        self.cache_dir = cache_dir
        self.max_patterns = max_patterns

        # OrderedDict for LRU (VAMS pattern)
        self._patterns: OrderedDict[str, dict] = OrderedDict()

        # Statistics (VAMS pattern)
        self._stats = {
            'total_repairs': 0,
            'patterns_learned': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }

    def add_pattern(self, pattern: dict):
        """Add pattern with LRU eviction."""
        pattern_id = pattern['pattern_id']

        if pattern_id in self._patterns:
            # Move to end (most recently used)
            self._patterns.move_to_end(pattern_id)
            self._patterns[pattern_id]['frequency'] += 1
            self._stats['cache_hits'] += 1
        else:
            # New pattern
            self._patterns[pattern_id] = pattern
            self._patterns.move_to_end(pattern_id)
            self._stats['cache_misses'] += 1
            self._stats['patterns_learned'] += 1

        # LRU eviction (VAMS technique)
        self._evict_if_needed()

        # Periodic save (VAMS: every 50 operations)
        if self._stats['total_repairs'] % 50 == 0:
            self._save()

    def _evict_if_needed(self):
        """Evict oldest patterns if over capacity."""
        while len(self._patterns) > self.max_patterns:
            oldest_key = next(iter(self._patterns))
            self._patterns.pop(oldest_key, None)
```

---

### 3. Knowledge Types & Categorization (from `knowledge_types.py`)

**VAMS Pattern**:
```python
class KnowledgeType(Enum):
    SUCCESS_PATTERN = "success_pattern"
    TOOL_DISCOVERY = "tool_discovery"
    INNOVATION = "innovation"
    LESSON = "lesson"
    DEBUG_PATTERN = "debug_pattern"

def knowledge_context(knowledge_type: KnowledgeType, domain: str, **kwargs):
    return {
        "knowledge_type": knowledge_type.value,
        "domain": domain,
        **kwargs
    }
```

**eClipLint Application**:
- Categorize repair patterns by type
- Track metrics per pattern type
- Filter patterns by category

**Implementation**:
```python
# python/clipfix/engines/pattern_types.py

from enum import Enum

class RepairPatternType(Enum):
    """Categorize repair patterns (VAMS-inspired)."""

    MISSING_SYNTAX = "missing_syntax"      # Missing colons, brackets, etc.
    INDENTATION = "indentation"            # Indentation errors
    STYLE_VIOLATION = "style_violation"    # PEP 8, Standard Style, etc.
    IMPORT_ISSUE = "import_issue"          # Missing imports
    QUOTE_STYLE = "quote_style"            # Quote inconsistency
    TYPE_ERROR = "type_error"              # Type-related errors
    SEMANTIC_ERROR = "semantic_error"      # Logic errors
    GENERAL = "general"                     # Other

def pattern_context(
    pattern_type: RepairPatternType,
    language: str,
    confidence: float,
    **kwargs
) -> dict:
    """Create standardized pattern context (VAMS pattern)."""
    return {
        "pattern_type": pattern_type.value,
        "language": language,
        "confidence": confidence,
        **kwargs
    }
```

---

### 4. Adaptive Thresholds & Confidence (from `adaptive_agent.py`)

**VAMS Pattern**:
```python
class AdaptiveAgentAdapter:
    THRESHOLD_AUTONOMOUS = 0.8  # High confidence → act independently
    THRESHOLD_CONSULT = 0.5     # Medium confidence → consult
    THRESHOLD_ESCALATE = 0.3    # Low confidence → escalate

    def recall_and_act(self, query: str, context: dict):
        result = self.router.recall_memory(query, context)
        confidence = result.get('confidence', 0.0)

        if confidence >= self.THRESHOLD_AUTONOMOUS:
            return {'action_mode': 'autonomous', ...}
        elif confidence >= self.THRESHOLD_CONSULT:
            return {'action_mode': 'consult', ...}
        else:
            return {'action_mode': 'escalate', ...}
```

**eClipLint Application**:
- Confidence thresholds for pattern reliability
- Only add patterns with high confidence to prompts
- Track pattern quality over time

**Implementation**:
```python
# python/clipfix/engines/agents/base_agent.py

class BaseAgent(ABC):
    # Pattern confidence thresholds (VAMS-inspired)
    CONFIDENCE_HIGH = 0.85       # Add to prompt immediately
    CONFIDENCE_MEDIUM = 0.65     # Add after 3+ occurrences
    CONFIDENCE_LOW = 0.45        # Monitor, don't use

    def _should_include_pattern(self, pattern: dict) -> bool:
        """
        Decide if pattern should be in prompt.
        Uses VAMS adaptive threshold pattern.
        """
        confidence = pattern.get('confidence', 0.0)
        frequency = pattern.get('frequency', 0)

        # High confidence → include immediately
        if confidence >= self.CONFIDENCE_HIGH:
            return True

        # Medium confidence → require frequency
        if confidence >= self.CONFIDENCE_MEDIUM and frequency >= 3:
            return True

        # Low confidence → exclude
        return False
```

---

### 5. Metrics & Quality Tracking (from `knowledge_types.py`)

**VAMS Pattern**:
```python
@dataclass
class KnowledgeMetrics:
    knowledge_type: KnowledgeType
    total_count: int = 0
    accepted_count: int = 0
    rejected_count: int = 0
    avg_confidence: float = 0.0

    @property
    def acceptance_rate(self) -> float:
        total = self.accepted_count + self.rejected_count
        return self.accepted_count / total if total > 0 else 0.0

    @property
    def quality_score(self) -> float:
        return self.acceptance_rate * self.avg_confidence
```

**eClipLint Application**:
- Track pattern effectiveness
- Compute quality scores
- Identify low-quality patterns for removal

**Implementation**:
```python
# python/clipfix/engines/pattern_metrics.py

@dataclass
class PatternMetrics:
    """VAMS-style quality metrics for repair patterns."""

    pattern_type: RepairPatternType
    total_uses: int = 0
    successful_uses: int = 0
    failed_uses: int = 0
    avg_repair_time_ms: float = 0.0

    @property
    def success_rate(self) -> float:
        """Success rate [0, 1]."""
        total = self.successful_uses + self.failed_uses
        return self.successful_uses / total if total > 0 else 0.0

    @property
    def quality_score(self) -> float:
        """
        Overall quality: higher success rate + faster repairs = better.
        VAMS-inspired: acceptance_rate * avg_confidence
        Adapted: success_rate * (1 / normalized_time)
        """
        if self.avg_repair_time_ms == 0:
            return self.success_rate

        # Normalize time (assume 5s = 5000ms is baseline)
        time_score = min(1.0, 5000 / self.avg_repair_time_ms)
        return self.success_rate * time_score
```

---

## Complete Architecture

### File Structure

```
~/.ecliplint/
├── knowledge_cache/
│   ├── python/
│   │   ├── patterns.json          # Learned patterns
│   │   ├── metrics.json           # Quality metrics
│   │   └── hashes.json            # SHA-256 registry
│   ├── javascript/
│   ├── bash/
│   ├── sql/
│   └── rust/
├── metrics.jsonl                   # Repair logs (for analysis)
└── config.yaml                     # User preferences
```

### Pattern JSON Structure (VAMS-inspired)

```json
{
  "patterns": [
    {
      "pattern_id": "a1b2c3d4e5f6",
      "pattern_type": "missing_syntax",
      "language": "python",
      "abstract_example": {
        "broken_pattern": "def IDENTIFIER(ARGS)\n    return EXPRESSION",
        "fixed_pattern": "def IDENTIFIER(ARGS):\n    return EXPRESSION"
      },
      "fix_instruction": "Add : after function definition",
      "frequency": 47,
      "confidence": 0.92,
      "first_seen": "2024-12-13T10:30:00Z",
      "last_seen": "2024-12-13T14:22:00Z",
      "success_rate": 0.98,
      "avg_repair_time_ms": 2345
    }
  ],
  "metadata": {
    "total_repairs": 1247,
    "patterns_learned": 23,
    "last_updated": "2024-12-13T14:22:00Z",
    "git_sha": "a1b2c3d4e5f67890"
  }
}
```

### Metrics JSON Structure

```json
{
  "python": {
    "missing_syntax": {
      "total_uses": 150,
      "successful_uses": 147,
      "failed_uses": 3,
      "success_rate": 0.98,
      "avg_repair_time_ms": 2345,
      "quality_score": 0.91
    },
    "indentation": {
      "total_uses": 89,
      "successful_uses": 85,
      "failed_uses": 4,
      "success_rate": 0.96,
      "avg_repair_time_ms": 2890,
      "quality_score": 0.88
    }
  }
}
```

---

## VAMS Integration Points

### 1. Pattern Learning Flow

```python
def repair(self, code: str) -> str:
    """Repair with VAMS-style learning."""

    # 1. Load knowledge (base + accumulated)
    knowledge = self._load_knowledge()

    # 2. Perform repair
    start_time = time.time()
    repaired = self._generate_repair(code, knowledge)
    repair_time_ms = (time.time() - start_time) * 1000

    # 3. Extract pattern (VAMS hash-based)
    pattern_hash = PatternHash.compute_pattern_hash(code, repaired, self.language)

    # 4. Check if duplicate (VAMS incremental cache)
    if not self.accumulator.is_duplicate(pattern_hash):
        pattern = self.pattern_learner.extract_pattern(
            code, repaired, self.language
        )

        # 5. Add to accumulator (VAMS LRU eviction)
        if pattern:
            self.accumulator.add_pattern(pattern)

    # 6. Update metrics (VAMS quality tracking)
    if self._is_valid_repair(code, repaired):
        self.metrics.record_success(self.language, repair_time_ms)
    else:
        self.metrics.record_failure(self.language)

    return repaired
```

### 2. Knowledge Merging (VAMS Adaptive Pattern)

```python
def _merge_knowledge(self, base: dict, accumulated: dict) -> dict:
    """
    Merge base + accumulated knowledge.
    Uses VAMS adaptive threshold + quality scoring.
    """
    merged = base.copy()

    patterns = accumulated.get("patterns", [])

    # Filter by confidence threshold (VAMS adaptive agent)
    high_quality = [
        p for p in patterns
        if self._should_include_pattern(p)
    ]

    # Sort by quality score (VAMS metrics)
    high_quality.sort(
        key=lambda p: p.get('quality_score', 0),
        reverse=True
    )

    # Take top 10 (VAMS: limit to most useful)
    top_patterns = high_quality[:10]

    # Format as instructional text
    if top_patterns:
        learned_section = self._format_learned_patterns(top_patterns)

        merged["repair_prompt"] = (
            base.get("repair_prompt", "") +
            "\n\n## YOUR COMMON PATTERNS (Learned from Your Repairs)\n\n" +
            learned_section +
            "\n\nPRIORITY: Check these patterns FIRST - you make these mistakes frequently."
        )

    return merged
```

### 3. Metrics Dashboard (VAMS-style)

```bash
$ ecliplint --learning-stats

eClipLint Learning Metrics
==========================

Python:
  Total repairs: 1,247
  Patterns learned: 23
  Success rate: 95.3% → 97.8% (+2.5%)

  Top Patterns (by quality score):
  1. Missing colon (47x, 98% success, quality: 0.91) ⭐
  2. Indentation (34x, 96% success, quality: 0.88)
  3. Missing import (23x, 91% success, quality: 0.85)

JavaScript:
  Total repairs: 543
  Patterns learned: 18
  Success rate: 93.1% → 96.4% (+3.3%)

  Top Patterns:
  1. Missing semicolon (31x, 99% success, quality: 0.93) ⭐
  2. Const/let (29x, 97% success, quality: 0.89)
```

---

## Privacy Guarantees (VAMS Hash-Based)

### What Gets Stored

✅ **Safe** (SHA-256 hashed or abstracted):
```python
{
  "pattern_id": "a1b2c3d4e5f6",  # SHA-256 hash
  "abstract_example": {
    "broken": "def IDENTIFIER(ARGS)\n    return EXPRESSION",
    "fixed": "def IDENTIFIER(ARGS):\n    return EXPRESSION"
  },
  "instruction": "Add : after function definition",
  "frequency": 47
}
```

❌ **Never Stored**:
```python
# Your actual code (never stored)
def calculate_payment(credit_card_number, amount):
    return process_transaction(credit_card_number, amount)

# Abstracted version (what's stored)
def IDENTIFIER(IDENTIFIER, IDENTIFIER):
    return IDENTIFIER(IDENTIFIER, IDENTIFIER)
```

### Hash-Based Deduplication

```python
# VAMS technique: Hash-based identity
pattern_hash = hashlib.sha256(
    f"{language}:{broken}:{fixed}".encode('utf-8')
).hexdigest()

# Result: "a1b2c3d4e5f67890..." (no code stored)
```

---

## Benefits Over Static System

| Feature | Static (Current) | VAMS-Inspired (Planned) |
|---------|-----------------|-------------------------|
| **Learning** | Manual curation | Automatic from repairs |
| **Personalization** | Generic prompts | YOUR common patterns |
| **Improvement** | Code changes needed | Self-improving |
| **Quality Tracking** | None | Metrics per pattern |
| **Deduplication** | None | SHA-256 hash-based |
| **Eviction** | None | LRU (bounded memory) |
| **Confidence** | None | Adaptive thresholds |
| **Categories** | None | Typed patterns |

---

## Implementation Checklist

### Phase 1: Pattern Extraction (Week 1)
- [ ] Create `pattern_learner.py` with hash-based extraction
- [ ] Implement `PatternHash` class (SHA-256)
- [ ] Implement pattern abstraction (remove specifics)
- [ ] Implement repair type classification
- [ ] Test privacy (verify no code leakage)

### Phase 2: Knowledge Accumulation (Week 2)
- [ ] Create `knowledge_accumulator.py`
- [ ] Implement OrderedDict LRU cache (VAMS pattern)
- [ ] Implement periodic saves (every 50 operations)
- [ ] Implement git-aware invalidation
- [ ] Add pattern frequency tracking

### Phase 3: Metrics & Quality (Week 3)
- [ ] Create `pattern_metrics.py`
- [ ] Implement quality scoring (VAMS pattern)
- [ ] Implement confidence thresholds
- [ ] Track success/failure rates
- [ ] Create metrics dashboard CLI

### Phase 4: Agent Integration (Week 4)
- [ ] Integrate into `base_agent.py`
- [ ] Implement knowledge merging
- [ ] Format patterns for prompts
- [ ] Test prompt personalization
- [ ] Validate improvement (94% → 97%+)

---

## Testing Strategy

### 1. Privacy Audit
```bash
# Verify no actual code in patterns
grep -r "calculate_payment" ~/.ecliplint/knowledge_cache/
# Should return: No matches

# Verify only abstract patterns
cat ~/.ecliplint/knowledge_cache/python/patterns.json | jq '.patterns[].abstract_example'
# Should show: IDENTIFIER, EXPRESSION, etc.
```

### 2. Quality Improvement
```bash
# Week 1 baseline
pytest tests/test_prompt_quality.py
# Python: 94.2% pass rate

# Week 4 after learning
pytest tests/test_prompt_quality.py
# Python: 97.8% pass rate ✓ (+3.6%)
```

### 3. Performance Overhead
```bash
# Measure learning overhead
time ecliplint  # Without learning: 2.3s
time ecliplint  # With learning: 2.35s (+2%, acceptable)
```

---

## VAMS Techniques Summary

| VAMS File | Technique | eClipLint Application |
|-----------|-----------|----------------------|
| `skill_cache.py` | SHA-256 hashing | Pattern deduplication |
| `incremental_cache.py` | LRU eviction | Bounded pattern storage |
| `incremental_cache.py` | Periodic saves | Save every 50 operations |
| `incremental_cache.py` | Git-aware | Invalidate on branch switch |
| `knowledge_types.py` | Categorization | Typed repair patterns |
| `knowledge_types.py` | Quality metrics | Success rate, quality score |
| `adaptive_agent.py` | Confidence thresholds | Pattern inclusion criteria |
| `adaptive_agent.py` | Statistics tracking | Repairs, patterns, rates |

---

## Future Enhancements

### Community Pattern Sharing (VAMS-inspired)

```bash
# Export your patterns (privacy-safe)
ecliplint --export-patterns python > python_web_frameworks.json

# Import community patterns
ecliplint --import-patterns python_beginner_errors.json
```

### Pattern Repository (GitHub)
```
github.com/deesatzed/eClipLint-patterns/
├── python/
│   ├── web_frameworks.json    (Django, Flask patterns)
│   ├── data_science.json      (NumPy, Pandas patterns)
│   └── beginner.json          (Common newbie mistakes)
├── javascript/
│   ├── react.json             (React patterns)
│   └── node.json              (Node.js patterns)
```

---

## References

- **VAMS Repository**: `/Volumes/WS4TB/vamswsbu1112/VAMS_WORKSPACE/core/vams`
- **VAMS README**: Incremental cache, adaptive agents, knowledge types
- **eClipLint Codebase**: `/Volumes/WS4TB/clipfix_production`

**Created**: 2024-12-13
**Status**: Designed, ready for implementation
**Approval**: User approved for future implementation
