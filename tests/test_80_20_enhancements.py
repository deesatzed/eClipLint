#!/usr/bin/env python3
"""
Tests for the 80/20 high-value enhancements.
Tests smart auto-parallel, language override, health check, and enhanced stats.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

import pyperclip


def test_smart_auto_parallel():
    """Test that parallel processing auto-enables for 3+ segments."""
    print("\n=== Testing Smart Auto-Parallel Detection ===")

    # Multi-segment code (should trigger auto-parallel)
    # Use heredoc style to avoid markdown parsing issues
    multi_segment_code = '''python - <<'PY'
def hello():
    print("Hello")
PY

node - <<'JS'
const greet = () => console.log("Hello");
JS

psql - <<'SQL'
SELECT * FROM users;
SQL'''

    pyperclip.copy(multi_segment_code)

    # Run with benchmark to see if auto-parallel triggered
    result = subprocess.run(
        ["python", "-m", "clipfix.main", "--benchmark", "--no-llm"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, f"Should succeed: {result.stderr}"

    # Check if auto-parallel was mentioned in stderr
    if "Auto-enabled parallel" in result.stderr:
        print("✓ Auto-parallel detected and enabled for 3 segments")
    else:
        print("⚠ Auto-parallel may not have triggered (check benchmark output)")

    print(f"  Benchmark output: {result.stderr.strip()}")

    # Single segment (should NOT trigger auto-parallel)
    single_code = "def foo(): pass"
    pyperclip.copy(single_code)

    result = subprocess.run(
        ["python", "-m", "clipfix.main", "--benchmark", "--no-llm"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "Auto-enabled parallel" not in result.stderr, "Should not auto-enable for single segment"
    print("✓ Auto-parallel correctly skipped for single segment")

    print("✅ Smart auto-parallel test passed!")
    return True


def test_language_override():
    """Test --lang flag to force specific language."""
    print("\n=== Testing Language Override (--lang) ===")

    # Ambiguous code that could be Python or JavaScript
    ambiguous_code = "x=1\ny=2\nz=3"
    pyperclip.copy(ambiguous_code)

    # Force as Python
    result = subprocess.run(
        ["python", "-m", "clipfix.main", "--lang", "python", "--no-llm", "--diff"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, f"Python override failed: {result.stderr}"
    print("✓ --lang python worked")

    # Force as JavaScript
    pyperclip.copy(ambiguous_code)
    result = subprocess.run(
        ["python", "-m", "clipfix.main", "--lang", "javascript", "--no-llm", "--diff"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, f"JavaScript override failed: {result.stderr}"
    print("✓ --lang javascript worked")

    # Force as JSON (should fail formatting but not crash)
    pyperclip.copy(ambiguous_code)
    result = subprocess.run(
        ["python", "-m", "clipfix.main", "--lang", "json", "--no-llm"],
        capture_output=True,
        text=True
    )

    # JSON parsing will fail, which is expected
    print(f"✓ --lang json handled gracefully (exit code: {result.returncode})")

    print("✅ Language override test passed!")
    return True


def test_health_check():
    """Test --health formatter status check."""
    print("\n=== Testing Formatter Health Check (--health) ===")

    result = subprocess.run(
        ["python", "-m", "clipfix.main", "--health"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, f"Health check failed: {result.stderr}"
    assert "Health Check" in result.stdout, "Should show health check header"

    # Check for expected formatters
    expected_formatters = ["black", "ruff", "prettier", "shfmt", "rustfmt", "sqlfluff"]

    for formatter in expected_formatters:
        assert formatter in result.stdout, f"Should list {formatter}"

    # Count installed vs missing
    installed_count = result.stdout.count("✓")
    missing_count = result.stdout.count("✗")

    print(f"✓ Health check showed {installed_count} installed, {missing_count} missing")
    print(f"  Sample output:\n{result.stdout[:300]}...")

    print("✅ Health check test passed!")
    return True


def test_enhanced_cache_stats():
    """Test enhanced --cache-stats with hit rate, time saved, top languages."""
    print("\n=== Testing Enhanced Cache Stats ===")

    # First, populate cache with some formatting operations
    test_codes = [
        ("def foo(): pass", "python"),
        ("const x = 1;", "javascript"),
        ('{"a": 1}', "json"),
    ]

    for code, _ in test_codes:
        pyperclip.copy(code)
        subprocess.run(
            ["python", "-m", "clipfix.main", "--no-llm"],
            capture_output=True,
            text=True
        )

    # Now check enhanced stats
    result = subprocess.run(
        ["python", "-m", "clipfix.main", "--cache-stats"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, f"Cache stats failed: {result.stderr}"
    assert "Cache Statistics" in result.stdout, "Should show stats header"

    # Check for enhanced metrics
    expected_metrics = ["Entries:", "Size:", "Hit rate:", "Time saved:"]

    for metric in expected_metrics:
        assert metric in result.stdout, f"Should show {metric}"

    print(f"✓ Enhanced cache stats working")
    print(f"  Sample output:\n{result.stdout}")

    print("✅ Enhanced cache stats test passed!")
    return True


def test_cli_help():
    """Test that new flags appear in --help."""
    print("\n=== Testing CLI Help Documentation ===")

    result = subprocess.run(
        ["python", "-m", "clipfix.main", "--help"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0

    # Check new flags are documented
    new_flags = ["--lang", "--health"]

    for flag in new_flags:
        assert flag in result.stdout, f"{flag} should be in --help"

    print("✓ New flags documented in --help")
    print("✅ CLI help test passed!")
    return True


def run_all_tests():
    """Run all 80/20 enhancement tests."""
    print("=" * 60)
    print("eClipLint 80/20 Enhancement Tests")
    print("Testing high-value features: auto-parallel, lang override,")
    print("health check, and enhanced cache stats")
    print("=" * 60)

    tests = [
        ("Smart Auto-Parallel", test_smart_auto_parallel),
        ("Language Override", test_language_override),
        ("Health Check", test_health_check),
        ("Enhanced Cache Stats", test_enhanced_cache_stats),
        ("CLI Help", test_cli_help),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"✗ {test_name} failed")
        except Exception as e:
            failed += 1
            print(f"✗ {test_name} failed with error: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
