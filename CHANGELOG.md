# Changelog

All notable changes to eClipLint will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-12-13

### Added

#### Multi-Agent Architecture
- **Language-specific specialist agents** for higher quality code repair
  - PythonAgent with PEP 8 expertise
  - JavaScriptAgent with ES6+ and Standard Style knowledge
  - BashAgent with shellcheck best practices
  - SQLAgent with PostgreSQL dialect support
  - RustAgent with rustfmt style guidelines
  - GenericAgent fallback for unsupported languages
- **ManagerAgent** for intelligent routing based on detected language
- **JSON knowledge bases** (community-editable) for each language
  - Comprehensive repair prompts with examples
  - Common error patterns and fixes
  - Language-specific style rules
  - Test cases for validation

#### UX Improvements
- **Progress feedback** during LLM operations
  - First-time model download warning with size estimate
  - Loading indicators for model and agent initialization
  - Step-by-step progress messages (classifying, repairing)
- **`--diff` flag** for non-destructive preview mode
  - Shows colored diff output (green additions, red deletions)
  - Allows review before clipboard modification
  - Works with `--no-llm` for fast formatting preview
- **Change summaries** on successful formatting
  - Reports lines modified, added, and removed
  - Clear "no changes needed" message when code is already correct
- **Improved help text** with detailed flag descriptions
- **Colored terminal output** with fallback for dumb terminals

#### Developer Experience
- Lazy loading of agents (instantiated only when needed)
- Shared LLM model instance across all agents (no redundant loads)
- Extensible architecture (add new languages by creating agent + JSON)
- Comprehensive error handling with actionable messages

### Changed
- **Renamed from clipfix to eClipLint** for better discoverability
- LLM repair now uses multi-agent system instead of single generic prompt
- Progress is now visible at every step (no more silent waits)
- Better terminal integration (respects TERM environment variable)

### Technical Details
- 7 JSON knowledge files with language-specific expertise
- 8 agent classes (6 specialists + generic + manager)
- Enhanced `main.py` with diff and summary functions
- Refactored `llm.py` for agent integration
- All Unicode output with ASCII fallback

### Known Limitations
- macOS Apple Silicon only (mlx-lm requirement)
- 4GB model download on first use
- LLM repair takes 2-5 seconds (vs. instant formatting)
- No Intel Mac support currently

### For Contributors
- JSON knowledge files can be improved via PRs (no code changes needed)
- See `knowledge/` directory for language-specific repair prompts
- Agent system is extensible (add new language in <50 lines)

---

## [Unreleased]

### Planned for v1.1
- Automated test suite for agent routing
- Integration tests for full pipeline
- Performance optimizations (formatter caching)
- Binary distribution via Homebrew

### Planned for v2.0
- Linux support (alternative LLM backend)
- Multi-level undo (history browser)
- Watch mode (auto-format on clipboard change)
- Streaming LLM output
- Plugin system for custom formatters

---

[1.0.0]: https://github.com/deesatzed/eClipLint/releases/tag/v1.0.0
