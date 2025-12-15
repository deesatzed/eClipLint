# eClipLint Plugins

This directory contains example plugin definitions for eClipLint's extensible formatter system.

## What are Plugins?

Plugins allow you to add support for new formatters without modifying eClipLint's source code. Each plugin is a simple TOML file that describes how to invoke a formatter.

## Plugin Locations

- **Built-in plugins**: `python/clipfix/plugins/` (shipped with eClipLint)
- **User plugins**: `~/.ecliplint/plugins/` (your custom plugins)

## Creating a Plugin

### 1. Create a TOML file

Create `~/.ecliplint/plugins/my_formatter.toml`:

```toml
[plugin]
name = "my-formatter"
version = "1.0.0"
description = "Description of your formatter"

[formatter]
languages = ["mylang"]
check_command = "my-fmt --version"
format_command = "my-fmt --format --stdin"
input_method = "stdin"
output_method = "stdout"

[formatter.exit_codes]
success = [0]
```

### 2. Test your plugin

```bash
# Copy code to clipboard
echo "unformatted code" | pbcopy

# Run eClipLint - it will auto-detect your plugin
ecliplint

# Check if formatter was used
ecliplint --benchmark
```

## Example Plugins

### prettier.toml
Full-featured prettier integration showing:
- Multiple language support
- Parser mapping
- Configuration flags
- Performance hints

### custom_sql.toml
Example of integrating a proprietary formatter:
- Company-specific tools
- Environment variables
- Custom exit codes
- License handling

### latex.toml
Academic document formatting:
- File-based input
- Complex configuration
- Warning handling

## Plugin Schema

### Required Fields

```toml
[plugin]
name = "unique-name"
version = "1.0.0"
description = "What this formatter does"

[formatter]
languages = ["lang1", "lang2"]  # Languages to handle
check_command = "fmt --version"  # Installation check
format_command = "fmt {code}"    # Format command
input_method = "stdin"           # How to pass code
output_method = "stdout"         # How to get result
```

### Optional Fields

```toml
[formatter.parser_map]
# Map language to formatter-specific parser
javascript = "babel"

[formatter.config]
# Additional command flags
flags = ["--flag1", "--flag2"]

[formatter.env]
# Environment variables to set
MY_VAR = "value"

[formatter.exit_codes]
# Exit codes and their meanings
success = [0]
warning = [1]
error = [2, 3, 4]

[performance]
batch_capable = true    # Can process multiple files
cache_results = true    # Results are deterministic
parallel_safe = true    # Thread-safe
speed_estimate = 50     # ms per KB
max_file_size = 1000    # KB
```

## Variables in Commands

These variables are available in `format_command`:

- `{code}` - The input code
- `{file}` - Path to temporary file (when input_method="file")
- `{language}` - Detected language
- `{parser}` - Mapped parser name (from parser_map)

## Input/Output Methods

### Input Methods
- `stdin` - Pass code via standard input (recommended)
- `file` - Write to temp file, pass filename
- `argument` - Pass code as command argument (limited size)

### Output Methods
- `stdout` - Read formatted code from standard output (recommended)
- `file` - Read from output file
- `in-place` - Formatter modifies input file directly

## Performance Tips

1. **Use stdin/stdout** when possible (faster than file I/O)
2. **Set `cache_results = true`** for deterministic formatters
3. **Set `parallel_safe = true`** if formatter is thread-safe
4. **Set `batch_capable = true`** if formatter can handle multiple inputs

## Troubleshooting

### Plugin not detected
- Check file is in `~/.ecliplint/plugins/`
- Ensure `.toml` extension
- Validate TOML syntax

### Formatter not found
- Run `check_command` manually
- Ensure formatter is in PATH
- Check environment variables

### Formatting fails
- Test `format_command` manually
- Check exit codes match actual formatter
- Verify input/output methods

## Contributing

Share your plugins! Submit a PR to add your plugin to the examples directory.

## Future Features

- Plugin marketplace
- Auto-download formatters
- Plugin dependencies
- Chained formatters
- Language detection plugins