# Hotkey Setup Guide for eClipLint

## Overview

**Desired workflow**:
1. User copies broken code snippet
2. User presses hotkey (e.g., `⌘⇧F`)
3. eClipLint formats/repairs code
4. Result goes back to clipboard
5. User pastes perfect code

**If repair fails**: Error message prepended to clipboard as comment.

---

## macOS Implementation Options

### Option 1: Automator + Keyboard Shortcut (Built-in, No Installation)

**Best for**: Most users, easiest setup

**Steps**:

1. **Open Automator**
   ```bash
   open -a Automator
   ```

2. **Create New Quick Action**
   - File → New → Quick Action
   - Workflow receives: "no input" in "any application"

3. **Add "Run Shell Script" action**
   - Search for "Run Shell Script" in left sidebar
   - Drag to workflow area
   - Set "Shell" to `/bin/bash`
   - Set "Pass input" to "as arguments"

4. **Paste this script**:
   ```bash
   #!/bin/bash
   # eClipLint hotkey handler

   # Run ecliplint (assumes installed in PATH)
   /usr/local/bin/ecliplint 2>&1

   # Return code:
   # 0 = success (formatted)
   # 1 = clipboard empty
   # 2 = error (repair failed)

   # Show notification (optional)
   if [ $? -eq 0 ]; then
     osascript -e 'display notification "Code formatted successfully" with title "eClipLint"'
   else
     osascript -e 'display notification "Formatting failed - see clipboard" with title "eClipLint"'
   fi
   ```

5. **Save**
   - File → Save
   - Name: "Format Code with eClipLint"

6. **Assign Keyboard Shortcut**
   - System Settings → Keyboard → Keyboard Shortcuts
   - Services → General → "Format Code with eClipLint"
   - Click "Add Shortcut"
   - Press `⌘⇧F` (or your preferred combo)

**Usage**:
```
1. Copy broken code
2. Press ⌘⇧F
3. Paste formatted code
```

---

### Option 2: Hammerspoon (Advanced, More Flexible)

**Best for**: Power users, custom workflows

**Installation**:
```bash
brew install hammerspoon
```

**Setup**:

1. **Create Hammerspoon config**
   ```bash
   mkdir -p ~/.hammerspoon
   cat > ~/.hammerspoon/init.lua << 'EOF'
-- eClipLint hotkey integration

function runEcliplint()
    -- Get current clipboard
    local before = hs.pasteboard.getContents()

    -- Run ecliplint
    local output, status = hs.execute("/usr/local/bin/ecliplint 2>&1", true)

    -- Get new clipboard
    local after = hs.pasteboard.getContents()

    -- Show notification
    if status then
        hs.notify.new({
            title = "eClipLint",
            informativeText = "Code formatted successfully",
            withdrawAfter = 2
        }):send()
    else
        hs.notify.new({
            title = "eClipLint",
            informativeText = "Formatting failed",
            withdrawAfter = 3
        }):send()
    end
end

-- Bind to Cmd+Shift+F
hs.hotkey.bind({"cmd", "shift"}, "F", runEcliplint)

-- Show notification on startup
hs.notify.new({
    title = "Hammerspoon",
    informativeText = "eClipLint hotkey ready (⌘⇧F)",
    withdrawAfter = 2
}):send()
EOF
```

2. **Start Hammerspoon**
   - Open Hammerspoon app
   - Enable "Launch Hammerspoon at login"
   - Reload config

**Usage**: Same as Option 1 (press `⌘⇧F`)

---

### Option 3: BetterTouchTool (Premium, Most Features)

**Best for**: Users who already own BTT

**Setup**:
1. Open BetterTouchTool
2. Keyboard → Add New Shortcut
3. Trigger: `⌘⇧F`
4. Action: Execute Shell Script
5. Script:
   ```bash
   /usr/local/bin/ecliplint 2>&1
   ```

---

### Option 4: Custom macOS App (Future Enhancement)

**Best for**: Distribution to non-technical users

**Features**:
- Menu bar app with icon
- Click icon or use hotkey
- Visual feedback (progress spinner)
- Settings panel

**Implementation**:
```swift
// Swift macOS app (future enhancement)
import Cocoa
import Carbon

class EcliplintApp: NSApplication {
    var statusItem: NSStatusItem?

    func applicationDidFinishLaunching() {
        // Create menu bar icon
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        statusItem?.button?.title = "✨"

        // Register hotkey
        registerHotkey()
    }

    func registerHotkey() {
        // Register Cmd+Shift+F
        let hotkey = MASShortcut(keyCode: kVK_ANSI_F, modifierFlags: [.command, .shift])
        MASShortcutBinder.shared().bindShortcut(hotkey) {
            self.runEcliplint()
        }
    }

    func runEcliplint() {
        // Show progress
        statusItem?.button?.title = "⏳"

        // Run ecliplint binary
        let task = Process()
        task.executableURL = URL(fileURLWithPath: "/usr/local/bin/ecliplint")
        task.launch()
        task.waitUntilExit()

        // Update icon based on result
        if task.terminationStatus == 0 {
            statusItem?.button?.title = "✅"
            showNotification(title: "eClipLint", message: "Code formatted")
        } else {
            statusItem?.button?.title = "❌"
            showNotification(title: "eClipLint", message: "Formatting failed")
        }

        // Reset icon after 2 seconds
        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
            self.statusItem?.button?.title = "✨"
        }
    }
}
```

---

## Error Comments in Clipboard

### Current Behavior

When `ecliplint` fails, it prints error to stderr and returns exit code 2:

```python
# In main.py
if not ok:
    print(f"✖ ecliplint failed: {mode}", file=sys.stderr)
    return 2
```

**Problem**: User doesn't know *what* failed (just sees no change).

---

### Improved Behavior: Error Comments

**Proposal**: When repair fails, prepend error as comment to clipboard.

**Example**:

User copies:
```python
x=1
 if x>0:
print(x
```

eClipLint tries to repair → fails (missing closing paren)

Clipboard becomes:
```python
# ❌ eClipLint: Repair failed - SyntaxError: unexpected EOF while parsing
# The AI could not fix this code. Possible issues:
# - Missing closing parenthesis on line 3
# - Original code may be incomplete
#
# Original code preserved below:

x=1
 if x>0:
print(x
```

**Benefits**:
- ✅ User knows **why** it failed
- ✅ Original code preserved (can still paste it)
- ✅ Actionable hints (what to fix manually)
- ✅ No data loss (clipboard still has code)

---

### Implementation

**Step 1: Update `main.py` to add error comments**

```python
def format_error_comment(error_msg: str, original_code: str, language: str = "python") -> str:
    """
    Prepend error message as comment to original code.

    Args:
        error_msg: Error message from formatter/repair
        original_code: Original broken code
        language: Detected language (for comment syntax)

    Returns:
        str: Original code with error comment prepended
    """
    # Choose comment syntax based on language
    comment_styles = {
        "python": "#",
        "javascript": "//",
        "typescript": "//",
        "bash": "#",
        "sql": "--",
        "rust": "//",
        "yaml": "#",
        "json": "",  # JSON doesn't support comments
    }

    comment = comment_styles.get(language, "#")

    # Build error message
    lines = [
        f"{comment} ❌ eClipLint: Repair failed",
        f"{comment} Error: {error_msg}",
        f"{comment}",
        f"{comment} The AI could not fix this code. Common reasons:",
        f"{comment} - Code is incomplete (missing closing brackets/braces)",
        f"{comment} - Syntax error is too complex for automated repair",
        f"{comment} - Code may need human review",
        f"{comment}",
        f"{comment} Original code preserved below:",
        f"{comment}",
    ]

    # Special case: JSON (no comments allowed)
    if language == "json":
        lines = [
            "/* ❌ eClipLint: Repair failed */",
            "/* Note: This is invalid JSON (comments not allowed) */",
            f"/* Error: {error_msg} */",
            "/* Fix manually and remove this comment */",
            "",
        ]

    return "\n".join(lines) + "\n" + original_code


def main(argv=None):
    # ... existing code ...

    ok, out, mode = process_text(raw, allow_llm=(not args.no_llm))

    if not ok:
        # Instead of just printing error, add to clipboard
        detected_lang = "python"  # TODO: Detect language before processing

        error_with_code = format_error_comment(mode, raw, detected_lang)

        # Write to clipboard
        pyperclip.copy(error_with_code)

        # Print to stderr (for terminal users)
        print(f"✖ ecliplint failed: {mode}", file=sys.stderr)
        print(f"⚠ Error message added to clipboard as comment", file=sys.stderr)

        return 2

    # ... rest of existing code ...
```

**Step 2: Detect language before processing** (so we know comment syntax)

```python
def detect_language_for_comments(text: str) -> str:
    """
    Quick language detection for comment syntax.

    Args:
        text: Code snippet

    Returns:
        str: Language name (python, javascript, bash, etc.)
    """
    from clipfix.engines.detect_and_format import _detect_kind
    from clipfix.engines.segmenter import regex_segment

    segs = regex_segment(text)
    if segs:
        seg = segs[0]
        return seg.inner_kind or _detect_kind(seg.text)

    return "python"  # Default fallback


def main(argv=None):
    # ... existing code ...

    raw = pyperclip.paste()
    if not raw or not raw.strip():
        print("✖ ecliplint: clipboard empty", file=sys.stderr)
        return 1

    # Detect language BEFORE processing
    detected_lang = detect_language_for_comments(raw)

    ok, out, mode = process_text(raw, allow_llm=(not args.no_llm))

    if not ok:
        error_with_code = format_error_comment(mode, raw, detected_lang)
        pyperclip.copy(error_with_code)
        print(f"✖ ecliplint failed: {mode}", file=sys.stderr)
        print(f"⚠ Error message added to clipboard as comment", file=sys.stderr)
        return 2

    # ... rest of code ...
```

---

### Example Outputs

**Python failure**:
```python
# ❌ eClipLint: Repair failed
# Error: repair+format error (python): invalid syntax
#
# The AI could not fix this code. Common reasons:
# - Code is incomplete (missing closing brackets/braces)
# - Syntax error is too complex for automated repair
# - Code may need human review
#
# Original code preserved below:

def foo(
    x = 1
```

**JavaScript failure**:
```javascript
// ❌ eClipLint: Repair failed
// Error: format error (javascript): Unexpected token
//
// The AI could not fix this code. Common reasons:
// - Code is incomplete (missing closing brackets/braces)
// - Syntax error is too complex for automated repair
// - Code may need human review
//
// Original code preserved below:

const obj = { a: 1, b: 2
```

**SQL failure**:
```sql
-- ❌ eClipLint: Repair failed
-- Error: format error (sql): syntax error at or near "FROM"
--
-- The AI could not fix this code. Common reasons:
-- - Code is incomplete (missing closing brackets/braces)
-- - Syntax error is too complex for automated repair
-- - Code may need human review
--
-- Original code preserved below:

SELECT id, name,
FROM users
```

---

## Complete User Experience

### Scenario 1: Success (Most Common)

```
1. User copies: x=1\n if x>0:\nprint(x)
2. User presses ⌘⇧F
3. Notification: "✅ eClipLint: Code formatted successfully"
4. Clipboard: x = 1\nif x > 0:\n    print(x)
5. User pastes perfect code
```

### Scenario 2: Partial Success (Repaired)

```
1. User copies: def foo(\nx=1
2. User presses ⌘⇧F
3. Notification: "✅ eClipLint: repaired+formatted (2 lines modified)"
4. Clipboard: def foo():\n    x = 1
5. User pastes (may notice changes)
```

### Scenario 3: Failure (Unfixable)

```
1. User copies: def foo(\nx=1  (missing closing paren, incomplete)
2. User presses ⌘⇧F
3. Notification: "❌ eClipLint: Formatting failed"
4. Clipboard:
   # ❌ eClipLint: Repair failed
   # Error: repair+format error (python): unexpected EOF
   #
   # Original code preserved below:

   def foo(
   x=1

5. User pastes, sees error, fixes manually
```

---

## Implementation Priority

### Phase 1: Error Comments (Week 1)
- [ ] Implement `format_error_comment()` in main.py
- [ ] Add language detection before processing
- [ ] Test with all languages

### Phase 2: Hotkey Documentation (Week 1)
- [ ] Add HOTKEY_SETUP.md to repo
- [ ] Update README with hotkey instructions
- [ ] Create video tutorial

### Phase 3: Automator Quick Action (Week 2)
- [ ] Create pre-built Automator workflow
- [ ] Distribute as downloadable .workflow file
- [ ] One-click installation

### Phase 4: Native macOS App (Future)
- [ ] Swift app with menu bar icon
- [ ] Visual feedback (progress spinner)
- [ ] Settings panel (choose formatter, hotkey, etc.)
- [ ] Distribution via GitHub Releases

---

## Testing Checklist

- [ ] Hotkey triggers ecliplint
- [ ] Success shows notification
- [ ] Failure shows notification
- [ ] Error comment uses correct syntax (# for Python, // for JS, etc.)
- [ ] Error message is actionable
- [ ] Original code preserved in clipboard
- [ ] Works across all applications (browser, terminal, IDE, notes)
- [ ] No conflicts with existing hotkeys

---

## User Feedback Improvements

Based on user testing:

1. **Make hotkey discoverable**: Show in README, mention in --help
2. **Customizable hotkey**: Let users choose their own
3. **Sound feedback**: Optional "ding" on success, "boop" on failure
4. **Visual feedback**: Menu bar icon changes color (green/red)
5. **Stats**: Show "Formatted 47 snippets this week" in menu

---

## Summary

**Hotkey setup**: 3 options (Automator, Hammerspoon, BTT) - Automator easiest

**Error comments**: Failed repairs get helpful comment prepended to clipboard

**User experience**:
- ✅ Copy → Hotkey → Paste (3 steps, zero context switching)
- ✅ Success: Clean code in clipboard
- ✅ Failure: Error message + original code (actionable feedback)
- ✅ No data loss: Original code always preserved

**Next**: Implement error comments, document hotkey setup in README.
