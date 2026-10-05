import time
import asyncio
from typing import Any, Optional, Dict
from collections import OrderedDict

class AsyncCache:
    """Thread-safe asynchronous in-memory cache with TTL and LRU eviction."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key not in self._cache:
                return None
            val, expiry = self._cache[key]
            if time.time() > expiry:
                del self._cache[key]
                return None
            # Move to end (most recently accessed)
            self._cache.move_to_end(key)
            return val

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        async with self._lock:
            ttl_seconds = ttl if ttl is not None else self.default_ttl
            expiry = time.time() + ttl_seconds
            if key in self._cache:
                self._cache[key] = (value, expiry)
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self.max_size:
                    # Pop least recently used
                    self._cache.popitem(last=False)
                self._cache[key] = (value, expiry)

    async def clear(self) -> None:
        async with self._lock:
            self._cache.clear()

    async def size(self) -> int:
        async with self._lock:
            return len(self._cache)

cache = AsyncCache()
