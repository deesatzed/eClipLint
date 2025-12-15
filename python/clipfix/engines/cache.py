"""
Caching layer for eClipLint formatter results.
Inspired by qlty's caching but simplified for clipboard use case.
Provides instant results for unchanged code.
"""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass, asdict
import tempfile
import fcntl


@dataclass
class CacheEntry:
    """Represents a cached formatting result."""
    code_hash: str           # SHA-256 hash of input code
    language: str            # Detected language
    formatter: str           # Formatter used (e.g., "black", "prettier")
    success: bool            # Whether formatting succeeded
    output: str              # Formatted code
    mode: str               # Mode/status string
    timestamp: float         # Unix timestamp when cached
    hit_count: int = 0       # Number of cache hits

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'CacheEntry':
        """Create from dictionary."""
        return cls(**data)


class FormatterCache:
    """
    Simple and fast cache for formatter results.

    Features:
    - Content-based caching (SHA-256 hash)
    - TTL-based expiration
    - LRU eviction when size limit reached
    - File-based persistence
    - Thread-safe operations
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        ttl_seconds: int = 86400,  # 24 hours default
        max_entries: int = 1000,
        max_size_mb: int = 50
    ):
        """
        Initialize formatter cache.

        Args:
            cache_dir: Directory to store cache. None = ~/.ecliplint/cache/
            ttl_seconds: Time-to-live for cache entries in seconds
            max_entries: Maximum number of cache entries
            max_size_mb: Maximum cache size in megabytes
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".ecliplint" / "cache"

        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self.max_size_mb = max_size_mb

        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Cache index file (maps hash -> cache file)
        self.index_file = self.cache_dir / "index.json"

        # In-memory cache for fast lookups
        self.memory_cache: Dict[str, CacheEntry] = {}

        # Load existing cache index
        self._load_index()

        # Clean expired entries on startup
        self._clean_expired()

    def _compute_hash(self, code: str, language: str) -> str:
        """
        Compute hash for cache key.

        Includes both code content and language to avoid collisions
        when same code is detected as different languages.
        """
        content = f"{language}:{code}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def get(
        self,
        code: str,
        language: str
    ) -> Optional[Tuple[bool, str, str]]:
        """
        Get formatted code from cache.

        Args:
            code: Input code to format
            language: Detected language

        Returns:
            (success, output, mode) if cached, None if not cached or expired
        """
        cache_key = self._compute_hash(code, language)

        # Check memory cache first
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]

            # Check if expired
            if time.time() - entry.timestamp > self.ttl_seconds:
                # Expired, remove from cache
                del self.memory_cache[cache_key]
                return None

            # Update hit count
            entry.hit_count += 1

            # Cache hit!
            return entry.success, entry.output, f"{entry.mode}:cached"

        # Check disk cache
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    entry = CacheEntry.from_dict(data)

                    # Check if expired
                    if time.time() - entry.timestamp > self.ttl_seconds:
                        # Expired, remove from cache
                        cache_file.unlink()
                        return None

                    # Load into memory cache
                    self.memory_cache[cache_key] = entry

                    # Update hit count
                    entry.hit_count += 1

                    return entry.success, entry.output, f"{entry.mode}:cached"
            except Exception:
                # Corrupted cache file, remove it
                cache_file.unlink()
                return None

        # Cache miss
        return None

    def put(
        self,
        code: str,
        language: str,
        formatter: str,
        success: bool,
        output: str,
        mode: str
    ) -> None:
        """
        Store formatted code in cache.

        Args:
            code: Input code
            language: Detected language
            formatter: Formatter used
            success: Whether formatting succeeded
            output: Formatted code
            mode: Mode/status string
        """
        # Don't cache LLM repairs (non-deterministic)
        if "llm" in mode.lower():
            return

        # Don't cache failures (might be transient)
        if not success:
            return

        cache_key = self._compute_hash(code, language)

        # Create cache entry
        entry = CacheEntry(
            code_hash=cache_key,
            language=language,
            formatter=formatter,
            success=success,
            output=output,
            mode=mode,
            timestamp=time.time(),
            hit_count=0
        )

        # Store in memory cache
        self.memory_cache[cache_key] = entry

        # Store on disk
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            # Write to temp file first (atomic write)
            with tempfile.NamedTemporaryFile(
                mode='w',
                dir=self.cache_dir,
                delete=False
            ) as tmp:
                json.dump(entry.to_dict(), tmp, indent=2)
                tmp_path = tmp.name

            # Atomic rename
            os.rename(tmp_path, cache_file)
        except Exception as e:
            # Cache write failed, not critical
            print(f"Cache write failed: {e}", file=os.sys.stderr)

        # Check cache limits
        self._enforce_limits()

    def _load_index(self) -> None:
        """Load cache index from disk."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    index = json.load(f)

                # Load entries into memory (up to a limit)
                for cache_key in list(index.keys())[:100]:  # Load first 100
                    cache_file = self.cache_dir / f"{cache_key}.json"
                    if cache_file.exists():
                        try:
                            with open(cache_file, 'r') as f:
                                data = json.load(f)
                                self.memory_cache[cache_key] = CacheEntry.from_dict(data)
                        except Exception:
                            # Corrupted entry, skip
                            pass
            except Exception:
                # Corrupted index, will be rebuilt
                pass

    def _save_index(self) -> None:
        """Save cache index to disk."""
        index = {}

        # Build index from cache files
        for cache_file in self.cache_dir.glob("*.json"):
            if cache_file != self.index_file:
                cache_key = cache_file.stem
                index[cache_key] = str(cache_file)

        # Save index
        try:
            with tempfile.NamedTemporaryFile(
                mode='w',
                dir=self.cache_dir,
                delete=False
            ) as tmp:
                json.dump(index, tmp, indent=2)
                tmp_path = tmp.name

            os.rename(tmp_path, self.index_file)
        except Exception:
            # Index save failed, not critical
            pass

    def _clean_expired(self) -> None:
        """Remove expired cache entries."""
        now = time.time()
        expired_files = []

        # Check all cache files
        for cache_file in self.cache_dir.glob("*.json"):
            if cache_file == self.index_file:
                continue

            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    timestamp = data.get('timestamp', 0)

                    if now - timestamp > self.ttl_seconds:
                        expired_files.append(cache_file)
            except Exception:
                # Corrupted file, mark for removal
                expired_files.append(cache_file)

        # Remove expired files
        for cache_file in expired_files:
            try:
                cache_file.unlink()
            except Exception:
                pass

        # Clear expired entries from memory cache
        expired_keys = []
        for key, entry in self.memory_cache.items():
            if now - entry.timestamp > self.ttl_seconds:
                expired_keys.append(key)

        for key in expired_keys:
            del self.memory_cache[key]

    def _enforce_limits(self) -> None:
        """Enforce cache size and entry limits."""
        # Count cache files
        cache_files = list(self.cache_dir.glob("*.json"))
        cache_files = [f for f in cache_files if f != self.index_file]

        # Check entry count
        if len(cache_files) > self.max_entries:
            # Sort by modification time (LRU)
            cache_files.sort(key=lambda f: f.stat().st_mtime)

            # Remove oldest entries
            to_remove = len(cache_files) - self.max_entries
            for cache_file in cache_files[:to_remove]:
                try:
                    cache_file.unlink()

                    # Remove from memory cache
                    cache_key = cache_file.stem
                    if cache_key in self.memory_cache:
                        del self.memory_cache[cache_key]
                except Exception:
                    pass

        # Check total size
        total_size = sum(f.stat().st_size for f in cache_files)
        max_size_bytes = self.max_size_mb * 1024 * 1024

        if total_size > max_size_bytes:
            # Sort by access time and hit count
            cache_entries = []
            for cache_file in cache_files:
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                        cache_entries.append((
                            cache_file,
                            data.get('hit_count', 0),
                            data.get('timestamp', 0)
                        ))
                except Exception:
                    # Corrupted file, mark for removal
                    cache_entries.append((cache_file, 0, 0))

            # Sort by hit count (ascending) then timestamp (ascending)
            # Remove least used and oldest first
            cache_entries.sort(key=lambda x: (x[1], x[2]))

            # Remove entries until under size limit
            current_size = total_size
            for cache_file, _, _ in cache_entries:
                if current_size <= max_size_bytes:
                    break

                try:
                    file_size = cache_file.stat().st_size
                    cache_file.unlink()
                    current_size -= file_size

                    # Remove from memory cache
                    cache_key = cache_file.stem
                    if cache_key in self.memory_cache:
                        del self.memory_cache[cache_key]
                except Exception:
                    pass

    def clear(self) -> None:
        """Clear all cache entries."""
        # Remove all cache files
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
            except Exception:
                pass

        # Clear memory cache
        self.memory_cache.clear()

    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        cache_files = list(self.cache_dir.glob("*.json"))
        cache_files = [f for f in cache_files if f != self.index_file]

        total_size = sum(f.stat().st_size for f in cache_files)

        # Calculate hit rate from memory cache
        total_hits = sum(e.hit_count for e in self.memory_cache.values())

        return {
            "entries": len(cache_files),
            "size_mb": total_size / (1024 * 1024),
            "memory_entries": len(self.memory_cache),
            "total_hits": total_hits,
            "ttl_hours": self.ttl_seconds / 3600,
            "max_entries": self.max_entries,
            "max_size_mb": self.max_size_mb,
        }


# Global cache instance
_cache = None


def get_formatter_cache(**kwargs) -> FormatterCache:
    """Get or create global formatter cache instance."""
    global _cache
    if _cache is None:
        _cache = FormatterCache(**kwargs)
    return _cache


def cache_get(code: str, language: str) -> Optional[Tuple[bool, str, str]]:
    """Convenience function to get from cache."""
    cache = get_formatter_cache()
    return cache.get(code, language)


def cache_put(
    code: str,
    language: str,
    formatter: str,
    success: bool,
    output: str,
    mode: str
) -> None:
    """Convenience function to put in cache."""
    cache = get_formatter_cache()
    cache.put(code, language, formatter, success, output, mode)


def clear_cache() -> None:
    """Clear all cache entries."""
    cache = get_formatter_cache()
    cache.clear()


def cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    cache = get_formatter_cache()
    return cache.stats()