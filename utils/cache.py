"""
LRU Cache utility for agent results.
Reduces duplicate LLM calls by caching results based on input hash.
"""

import hashlib
import json
from functools import wraps
from typing import Any, Dict, Optional


class AgentCache:
    """In-memory LRU cache for agent results."""

    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Any] = {}
        self.access_order: list = []
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def _compute_key(self, *args, **kwargs) -> str:
        """Compute hash key from args and kwargs."""
        key_data = {
            "args": [str(a) for a in args],
            "kwargs": {k: str(v) for k, v in sorted(kwargs.items())}
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get cached result by key."""
        if key in self.cache:
            self.hits += 1
            # Move to end of access order (most recently used)
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        self.misses += 1
        return None

    def set(self, key: str, value: Any) -> None:
        """Set cached result with key."""
        if key in self.cache:
            self.access_order.remove(key)
        elif len(self.cache) >= self.max_size:
            # Remove least recently used
            oldest_key = self.access_order.pop(0)
            del self.cache[oldest_key]

        self.cache[key] = value
        self.access_order.append(key)

    def clear(self) -> None:
        """Clear all cached results."""
        self.cache.clear()
        self.access_order.clear()

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hits / total if total > 0 else 0,
            "size": len(self.cache),
            "max_size": self.max_size
        }


# Global cache instance
_agent_cache = AgentCache(max_size=500)


def cached_agent(func):
    """Decorator to cache agent results."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Compute cache key
        key = _agent_cache._compute_key(*args, **kwargs)

        # Try cache first
        cached_result = _agent_cache.get(key)
        if cached_result is not None:
            return cached_result

        # Call actual function
        result = func(*args, **kwargs)

        # Cache the result (only if no error)
        if result and "error" not in result:
            _agent_cache.set(key, result)

        return result

    wrapper.cache = _agent_cache
    return wrapper


def get_cache_stats() -> dict:
    """Get global cache statistics."""
    return _agent_cache.get_stats()


def clear_cache() -> None:
    """Clear global agent cache."""
    _agent_cache.clear()


if __name__ == "__main__":
    # Test cache
    @cached_agent
    def test_agent(text: str) -> dict:
        import time
        time.sleep(0.1)  # Simulate API call
        return {"result": text.upper()}

    # First call (miss)
    result1 = test_agent("hello")
    print(f"First call: {result1}")

    # Second call (hit)
    result2 = test_agent("hello")
    print(f"Second call: {result2}")

    # Different input (miss)
    result3 = test_agent("world")
    print(f"Third call: {result3}")

    print(f"Cache stats: {get_cache_stats()}")
