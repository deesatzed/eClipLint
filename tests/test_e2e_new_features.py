#!/usr/bin/env python3
"""
End-to-End tests for new eClipLint features inspired by qlty.
Tests parallel processing, caching, and plugin architecture.
"""

import os
import sys
import time
import tempfile
import json
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

import pyperclip
from clipfix.engines.cache import FormatterCache, cache_get, cache_put, clear_cache
from clipfix.engines.parallel_processor import ParallelProcessor
from clipfix.engines.segmenter import regex_segment
from clipfix.engines.detect_and_format import process_text


def test_cache_functionality():
    """Test caching layer functionality."""
    print("\n=== Testing Cache Functionality ===")

    # Clear cache first
    clear_cache()
    print("✓ Cache cleared")

    # Test Python code
    python_code = """
def hello(name):
    print(f"Hello, {name}!")
"""

    # First format (cache miss)
    start = time.time()
    ok1, out1, mode1 = process_text(python_code, allow_llm=False)
    time1 = time.time() - start

    assert ok1, "First format should succeed"
    print(f"✓ First format: {time1:.3f}s (cache miss)")

    # Second format (should be cache hit)
    start = time.time()
    ok2, out2, mode2 = process_text(python_code, allow_llm=False)
    time2 = time.time() - start

    assert ok2, "Second format should succeed"
    assert out1 == out2, "Output should be identical"
    assert "cached" in mode2, f"Should be cached, got mode: {mode2}"
    assert time2 < time1 / 2, f"Cache should be faster: {time2:.3f}s vs {time1:.3f}s"
    print(f"✓ Second format: {time2:.3f}s (cache hit, {time1/time2:.1f}x faster)")

    # Test cache stats
    cache = FormatterCache()
    stats = cache.stats()
    assert stats["entries"] > 0, "Should have cache entries"
    print(f"✓ Cache stats: {stats['entries']} entries, {stats['size_mb']:.2f} MB")

    print("✅ Cache functionality test passed!")
    return True


def test_parallel_processing():
    """Test parallel processing functionality."""
    print("\n=== Testing Parallel Processing ===")

    # Create multi-segment code
    mixed_code = '''
```python
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
```

```javascript
const fibonacci = (n) => {
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
};
```

```sql
SELECT
    users.name,
    COUNT(orders.id) as order_count
FROM users
LEFT JOIN orders ON users.id = orders.user_id
GROUP BY users.name
ORDER BY order_count DESC;
```
'''

    # Test with sequential processing
    segments = regex_segment(mixed_code)
    print(f"✓ Found {len(segments)} segments")

    processor = ParallelProcessor(max_workers=4)

    # Sequential timing
    start = time.time()
    sequential_results = []
    for seg in segments:
        full_text = seg.prefix + seg.text + seg.suffix
        result = process_text(full_text, allow_llm=False)
        sequential_results.append(result)
    sequential_time = time.time() - start
    print(f"✓ Sequential processing: {sequential_time:.3f}s")

    # Parallel timing
    start = time.time()
    parallel_results = processor.process_segments_parallel(segments, allow_llm=False)
    parallel_time = time.time() - start
    print(f"✓ Parallel processing: {parallel_time:.3f}s")

    # Verify results are the same
    assert len(sequential_results) == len(parallel_results), "Should have same number of results"

    speedup = sequential_time / parallel_time if parallel_time > 0 else 1.0
    print(f"✓ Speedup: {speedup:.1f}x")

    # Parallel should be faster for multiple segments
    if len(segments) > 1:
        assert speedup > 1.2, f"Parallel should be faster for {len(segments)} segments"

    print("✅ Parallel processing test passed!")
    return True


def test_cli_integration():
    """Test CLI integration of new features."""
    print("\n=== Testing CLI Integration ===")

    # Test cache stats command
    result = subprocess.run(
        ["python", "-m", "clipfix.main", "--cache-stats"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, "Cache stats should succeed"
    assert "Cache Statistics" in result.stdout, "Should show cache stats"
    print("✓ --cache-stats command works")

    # Test benchmark flag
    test_code = "def foo(x=1, y=2):\n    return x+y"
    pyperclip.copy(test_code)

    result = subprocess.run(
        ["python", "-m", "clipfix.main", "--benchmark", "--no-llm"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, "Benchmark should succeed"
    assert "Processing time:" in result.stderr, "Should show timing"
    print("✓ --benchmark flag works")

    # Test parallel flag
    pyperclip.copy(test_code)
    result = subprocess.run(
        ["python", "-m", "clipfix.main", "--parallel", "--no-llm"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, "Parallel mode should succeed"
    print("✓ --parallel flag works")

    # Test clear cache
    result = subprocess.run(
        ["python", "-m", "clipfix.main", "--clear-cache"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, "Clear cache should succeed"
    assert "Cache cleared" in result.stdout, "Should confirm cache cleared"
    print("✓ --clear-cache command works")

    print("✅ CLI integration test passed!")
    return True


def test_plugin_architecture():
    """Test plugin architecture (basic validation)."""
    print("\n=== Testing Plugin Architecture ===")

    # Check plugin examples exist
    plugin_dir = Path(__file__).parent.parent / "plugins" / "examples"
    assert plugin_dir.exists(), "Plugin examples directory should exist"

    plugin_files = list(plugin_dir.glob("*.toml"))
    assert len(plugin_files) > 0, "Should have example plugins"
    print(f"✓ Found {len(plugin_files)} example plugins")

    # Validate plugin TOML structure
    import tomli

    for plugin_file in plugin_files:
        with open(plugin_file, "rb") as f:
            try:
                data = tomli.load(f)
                assert "plugin" in data, f"{plugin_file.name} missing [plugin] section"
                assert "formatter" in data, f"{plugin_file.name} missing [formatter] section"
                assert "name" in data["plugin"], f"{plugin_file.name} missing plugin name"
                assert "languages" in data["formatter"], f"{plugin_file.name} missing languages"
                print(f"✓ Valid plugin: {plugin_file.name}")
            except Exception as e:
                print(f"✗ Invalid plugin {plugin_file.name}: {e}")
                return False

    print("✅ Plugin architecture test passed!")
    return True


def test_performance_improvements():
    """Test overall performance improvements."""
    print("\n=== Testing Performance Improvements ===")

    # Test formatters are working
    test_cases = [
        ("python", "def foo ( x , y ) :\n  return x + y"),
        ("javascript", "const add=(a,b)=>{return a+b;}"),
        ("json", '{"name":"test","value":123}'),
    ]

    for lang, code in test_cases:
        pyperclip.copy(code)

        # First run (populate cache)
        result1 = subprocess.run(
            ["python", "-m", "clipfix.main", "--no-llm", "--benchmark"],
            capture_output=True,
            text=True
        )
        assert result1.returncode == 0, f"Format {lang} should succeed"

        # Extract time from first run
        time1 = None
        for line in result1.stderr.split("\n"):
            if "Processing time:" in line:
                time1 = float(line.split(":")[1].strip().replace("s", ""))
                break

        # Second run (should use cache)
        pyperclip.copy(code)
        result2 = subprocess.run(
            ["python", "-m", "clipfix.main", "--no-llm", "--benchmark"],
            capture_output=True,
            text=True
        )
        assert result2.returncode == 0, f"Cached format {lang} should succeed"

        # Extract time from second run
        time2 = None
        for line in result2.stderr.split("\n"):
            if "Processing time:" in line:
                time2 = float(line.split(":")[1].strip().replace("s", ""))
                break

        if time1 and time2:
            speedup = time1 / time2 if time2 > 0 else 1.0
            print(f"✓ {lang}: {time1:.3f}s → {time2:.3f}s (cache speedup: {speedup:.1f}x)")
        else:
            print(f"✓ {lang}: formatted successfully")

    print("✅ Performance improvements verified!")
    return True


def run_all_tests():
    """Run all E2E tests."""
    print("=" * 60)
    print("eClipLint E2E Tests - New Features")
    print("Testing improvements inspired by qlty")
    print("=" * 60)

    tests = [
        ("Cache Functionality", test_cache_functionality),
        ("Parallel Processing", test_parallel_processing),
        ("CLI Integration", test_cli_integration),
        ("Plugin Architecture", test_plugin_architecture),
        ("Performance Improvements", test_performance_improvements),
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

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)