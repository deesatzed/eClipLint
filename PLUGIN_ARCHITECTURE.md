# eClipLint Plugin Architecture Design

## Overview

This document outlines the plugin architecture for eClipLint, inspired by qlty's successful plugin system but simplified for clipboard formatting use cases.

---

## Goals

1. **Extensibility**: Allow users to add custom formatters without modifying core code
2. **Simplicity**: Keep plugin definitions simple (TOML format)
3. **Performance**: Maintain sub-second formatting speeds
4. **Compatibility**: Work with existing formatters

---

## Plugin Structure

### Location

Plugins will be stored in:
- **Built-in**: `python/clipfix/plugins/` (shipped with eClipLint)
- **User**: `~/.ecliplint/plugins/` (user-defined custom plugins)

### Plugin Definition Format (plugin.toml)

```toml
# Example: prettier plugin
[plugin]
name = "prettier"
version = "1.0.0"
description = "JavaScript/TypeScript formatter"
author = "eClipLint"

[formatter]
# Languages this formatter handles
languages = ["javascript", "typescript", "json", "yaml", "css", "html"]

# Command to check if formatter is installed
check_command = "prettier --version"

# The actual format command
# Variables: {code} = input code, {file} = temp file path, {language} = detected language
format_command = "prettier --parser {language} --stdin"

# How to pass code to formatter
input_method = "stdin"  # Options: stdin, file, argument

# How formatter returns formatted code
output_method = "stdout"  # Options: stdout, file, in-place

# Parser mapping (language -> prettier parser name)
[formatter.parser_map]
javascript = "babel"
typescript = "typescript"
json = "json"
yaml = "yaml"
css = "css"
html = "html"

# Exit codes
[formatter.exit_codes]
success = [0]
parse_error = [2]

# Performance hints
[performance]
batch_capable = true  # Can process multiple files at once
cache_results = true  # Results can be cached
parallel_safe = true  # Thread-safe for parallel execution
```

---

## Core Plugin Types

### 1. Built-in Plugins

Pre-configured plugins for common formatters:

```
plugins/
├── prettier.toml       # JS/TS/JSON/YAML
├── black.toml          # Python
├── ruff.toml           # Python (alternative)
├── rustfmt.toml        # Rust
├── shfmt.toml          # Bash/Shell
├── sqlfluff.toml       # SQL
└── gofmt.toml          # Go (future)
```

### 2. User Plugins

Custom formatters for proprietary or niche languages:

```
~/.ecliplint/plugins/
├── custom_sql.toml     # Company-specific SQL dialect
├── proprietary.toml    # Internal language formatter
└── latex_fmt.toml      # LaTeX formatter
```

---

## Plugin Loader Implementation

### Python Implementation

```python
# python/clipfix/plugins/loader.py

import os
import tomli
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class FormatterPlugin:
    """Represents a formatter plugin."""
    name: str
    version: str
    description: str
    languages: List[str]
    check_command: str
    format_command: str
    input_method: str  # stdin, file, argument
    output_method: str  # stdout, file, in-place
    parser_map: Dict[str, str]
    exit_codes: Dict[str, List[int]]
    batch_capable: bool = False
    cache_results: bool = True
    parallel_safe: bool = True

    def is_available(self) -> bool:
        """Check if formatter is installed."""
        try:
            result = subprocess.run(
                self.check_command.split(),
                capture_output=True,
                timeout=1
            )
            return result.returncode == 0
        except:
            return False

    def format(self, code: str, language: str) -> Tuple[bool, str]:
        """Format code using this plugin."""
        # Map language to parser if needed
        parser = self.parser_map.get(language, language)

        # Build command
        cmd = self.format_command.replace("{language}", parser)

        # Execute based on input_method
        if self.input_method == "stdin":
            result = subprocess.run(
                cmd.split(),
                input=code,
                capture_output=True,
                text=True,
                timeout=5
            )
        elif self.input_method == "file":
            # Write to temp file, format, read back
            with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{language}') as f:
                f.write(code)
                f.flush()
                cmd = cmd.replace("{file}", f.name)
                result = subprocess.run(cmd.split(), capture_output=True, text=True)

        # Check exit code
        if result.returncode in self.exit_codes.get("success", [0]):
            return True, result.stdout
        else:
            return False, code


class PluginLoader:
    """Loads and manages formatter plugins."""

    def __init__(self):
        self.plugins: Dict[str, FormatterPlugin] = {}
        self.language_map: Dict[str, List[str]] = {}  # language -> [plugin_names]
        self._load_all_plugins()

    def _load_all_plugins(self):
        """Load built-in and user plugins."""
        # Load built-in plugins
        builtin_dir = Path(__file__).parent / "definitions"
        self._load_plugins_from_dir(builtin_dir)

        # Load user plugins
        user_dir = Path.home() / ".ecliplint" / "plugins"
        if user_dir.exists():
            self._load_plugins_from_dir(user_dir)

    def _load_plugins_from_dir(self, directory: Path):
        """Load all .toml plugins from a directory."""
        for toml_file in directory.glob("*.toml"):
            try:
                with open(toml_file, 'rb') as f:
                    data = tomli.load(f)
                    plugin = self._create_plugin(data)
                    self.plugins[plugin.name] = plugin

                    # Update language map
                    for lang in plugin.languages:
                        if lang not in self.language_map:
                            self.language_map[lang] = []
                        self.language_map[lang].append(plugin.name)

            except Exception as e:
                print(f"Failed to load plugin {toml_file}: {e}", file=sys.stderr)

    def _create_plugin(self, data: dict) -> FormatterPlugin:
        """Create plugin from TOML data."""
        return FormatterPlugin(
            name=data['plugin']['name'],
            version=data['plugin']['version'],
            description=data['plugin']['description'],
            languages=data['formatter']['languages'],
            check_command=data['formatter']['check_command'],
            format_command=data['formatter']['format_command'],
            input_method=data['formatter'].get('input_method', 'stdin'),
            output_method=data['formatter'].get('output_method', 'stdout'),
            parser_map=data['formatter'].get('parser_map', {}),
            exit_codes=data['formatter'].get('exit_codes', {'success': [0]}),
            batch_capable=data.get('performance', {}).get('batch_capable', False),
            cache_results=data.get('performance', {}).get('cache_results', True),
            parallel_safe=data.get('performance', {}).get('parallel_safe', True),
        )

    def get_formatter_for_language(self, language: str) -> Optional[FormatterPlugin]:
        """Get the best available formatter for a language."""
        plugin_names = self.language_map.get(language, [])

        # Return first available formatter
        for name in plugin_names:
            plugin = self.plugins[name]
            if plugin.is_available():
                return plugin

        return None

    def list_plugins(self) -> List[FormatterPlugin]:
        """List all loaded plugins."""
        return list(self.plugins.values())
```

---

## Integration with Existing Code

### Modify detect_and_format.py

```python
# python/clipfix/engines/detect_and_format.py

from ..plugins.loader import PluginLoader

# Initialize plugin loader globally
PLUGIN_LOADER = PluginLoader()

def _format_code(code: str, kind: str) -> Tuple[bool, str, str]:
    """Format code - now plugin-aware."""

    # First, try plugin system
    plugin = PLUGIN_LOADER.get_formatter_for_language(kind)
    if plugin:
        success, formatted = plugin.format(code, kind)
        if success:
            return True, formatted, f"plugin:{plugin.name}"

    # Fall back to existing hardcoded formatters
    # (existing code remains as fallback)
    ...
```

---

## Example User Plugin

### Custom SQL Formatter

`~/.ecliplint/plugins/custom_sql.toml`:

```toml
[plugin]
name = "custom-sql"
version = "1.0.0"
description = "Company-specific SQL formatter"
author = "ACME Corp"

[formatter]
languages = ["sql", "plsql"]
check_command = "acme-sql-fmt --version"
format_command = "acme-sql-fmt --style=company --stdin"
input_method = "stdin"
output_method = "stdout"

[formatter.exit_codes]
success = [0]
parse_error = [1]

[performance]
batch_capable = false
cache_results = true
parallel_safe = true
```

---

## Performance Considerations

### Caching

Cache plugin availability checks:

```python
class PluginLoader:
    def __init__(self):
        self._availability_cache = {}  # plugin_name -> bool
        self._cache_ttl = 300  # 5 minutes

    def is_available(self, plugin_name: str) -> bool:
        # Check cache first
        if plugin_name in self._availability_cache:
            return self._availability_cache[plugin_name]

        # Check and cache
        available = self.plugins[plugin_name].is_available()
        self._availability_cache[plugin_name] = available
        return available
```

### Parallel Safety

Plugins marked as `parallel_safe = true` can be run concurrently:

```python
def format_parallel(segments: List[Segment]) -> List[Segment]:
    """Format segments in parallel using plugins."""

    # Group by plugin and parallel safety
    parallel_segments = []
    sequential_segments = []

    for segment in segments:
        plugin = PLUGIN_LOADER.get_formatter_for_language(segment.language)
        if plugin and plugin.parallel_safe:
            parallel_segments.append((segment, plugin))
        else:
            sequential_segments.append((segment, plugin))

    # Process parallel segments concurrently
    with multiprocessing.Pool() as pool:
        parallel_results = pool.map(format_with_plugin, parallel_segments)

    # Process sequential segments one by one
    sequential_results = [format_with_plugin(s) for s in sequential_segments]

    return parallel_results + sequential_results
```

---

## Benefits

1. **User Extensibility**: Add support for any formatter without code changes
2. **Clean Separation**: Core logic separated from formatter definitions
3. **Easy Testing**: Each plugin can be tested independently
4. **Performance**: Plugins declare capabilities (batching, caching, parallelism)
5. **Future-Proof**: New formatters just need a TOML file

---

## Migration Plan

### Phase 1: Plugin Infrastructure (2 days)
- Create plugin loader
- Define TOML schema
- Add plugin discovery logic

### Phase 2: Migrate Existing Formatters (1 day)
- Convert hardcoded formatters to plugins
- Create TOML files for: black, ruff, prettier, shfmt, rustfmt, sqlfluff
- Keep hardcoded versions as fallback

### Phase 3: User Plugin Support (1 day)
- Add ~/.ecliplint/plugins/ directory support
- Documentation for creating custom plugins
- Example plugin templates

### Phase 4: Performance Features (2 days)
- Add caching layer
- Implement parallel processing
- Add batching support

---

## Testing Strategy

1. **Unit Tests**: Test plugin loader independently
2. **Integration Tests**: Test with real formatters
3. **Performance Tests**: Measure overhead of plugin system
4. **User Plugin Tests**: Test custom plugin loading

---

## Documentation

### For Users

**Creating a Custom Plugin**:

1. Create `~/.ecliplint/plugins/my_formatter.toml`
2. Define plugin metadata and formatter configuration
3. Test with: `ecliplint --list-plugins`
4. Use normally - eClipLint will auto-detect

### For Developers

**Adding a Built-in Plugin**:

1. Create `python/clipfix/plugins/definitions/new_formatter.toml`
2. Test with existing test suite
3. Document supported languages
4. Submit PR

---

## Future Enhancements

1. **Plugin Marketplace**: Share plugins via GitHub
2. **Plugin Validation**: Schema validation for TOML files
3. **Plugin Priorities**: User preference for formatter selection
4. **Plugin Chaining**: Multiple formatters in sequence
5. **Language Detection Plugins**: Custom language detection logic

---

## Summary

This plugin architecture provides the extensibility of qlty while maintaining eClipLint's simplicity and performance. Users can add custom formatters with a simple TOML file, while the core system remains fast and focused on clipboard formatting.