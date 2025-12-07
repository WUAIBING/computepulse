"""
Cache Layer for AI Orchestrator

Provides caching functionality to avoid redundant AI model calls.
Implements TTL-based cache with LRU eviction.
"""

import hashlib
import json
import time
import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
from collections import OrderedDict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Single cache entry with metadata."""
    key: str
    value: Any
    created_at: float
    expires_at: float
    hit_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    task_type: Optional[str] = None
    models_used: List[str] = field(default_factory=list)

    @property
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return time.time() > self.expires_at

    @property
    def age_seconds(self) -> float:
        """Get age of entry in seconds."""
        return time.time() - self.created_at


@dataclass
class CacheStats:
    """Cache statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expired_removals: int = 0
    total_entries: int = 0
    memory_usage_estimate: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0


class ResponseCache:
    """
    LRU Cache with TTL for AI model responses.

    Features:
    - TTL-based expiration
    - LRU eviction when max size reached
    - Prompt-based key generation
    - Cache statistics tracking
    - Thread-safe operations
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl_seconds: float = 3600.0,  # 1 hour default
        cleanup_interval_seconds: float = 300.0  # 5 minutes
    ):
        """
        Initialize cache.

        Args:
            max_size: Maximum number of entries
            default_ttl_seconds: Default time-to-live for entries
            cleanup_interval_seconds: Interval for automatic cleanup
        """
        self.max_size = max_size
        self.default_ttl = default_ttl_seconds
        self.cleanup_interval = cleanup_interval_seconds

        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._stats = CacheStats()
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None

    def _generate_key(
        self,
        prompt: str,
        task_type: Optional[str] = None,
        quality_threshold: Optional[float] = None,
        cost_limit: Optional[float] = None
    ) -> str:
        """
        Generate cache key from request parameters.

        Args:
            prompt: The request prompt
            task_type: Optional task type
            quality_threshold: Optional quality threshold
            cost_limit: Optional cost limit

        Returns:
            SHA256 hash as cache key
        """
        key_parts = [
            prompt.strip().lower(),
            str(task_type) if task_type else "",
            f"q{quality_threshold:.2f}" if quality_threshold else "",
            f"c{cost_limit:.2f}" if cost_limit else ""
        ]
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]

    async def get(
        self,
        prompt: str,
        task_type: Optional[str] = None,
        quality_threshold: Optional[float] = None,
        cost_limit: Optional[float] = None
    ) -> Optional[Any]:
        """
        Get cached response if available and not expired.

        Args:
            prompt: The request prompt
            task_type: Optional task type
            quality_threshold: Optional quality threshold
            cost_limit: Optional cost limit

        Returns:
            Cached value or None if not found/expired
        """
        key = self._generate_key(prompt, task_type, quality_threshold, cost_limit)

        async with self._lock:
            if key not in self._cache:
                self._stats.misses += 1
                return None

            entry = self._cache[key]

            if entry.is_expired:
                del self._cache[key]
                self._stats.misses += 1
                self._stats.expired_removals += 1
                logger.debug(f"Cache entry expired: {key[:8]}...")
                return None

            # Update access metadata (LRU)
            entry.hit_count += 1
            entry.last_accessed = time.time()
            self._cache.move_to_end(key)

            self._stats.hits += 1
            logger.debug(f"Cache hit: {key[:8]}... (hits: {entry.hit_count})")

            return entry.value

    async def set(
        self,
        prompt: str,
        value: Any,
        task_type: Optional[str] = None,
        quality_threshold: Optional[float] = None,
        cost_limit: Optional[float] = None,
        ttl_seconds: Optional[float] = None,
        models_used: Optional[List[str]] = None
    ) -> None:
        """
        Cache a response.

        Args:
            prompt: The request prompt
            value: Value to cache
            task_type: Optional task type
            quality_threshold: Optional quality threshold
            cost_limit: Optional cost limit
            ttl_seconds: Custom TTL (uses default if not specified)
            models_used: List of models that generated this response
        """
        key = self._generate_key(prompt, task_type, quality_threshold, cost_limit)
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl

        async with self._lock:
            # Evict if at capacity
            while len(self._cache) >= self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats.evictions += 1
                logger.debug(f"Cache eviction (LRU): {oldest_key[:8]}...")

            now = time.time()
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                expires_at=now + ttl,
                task_type=task_type,
                models_used=models_used or []
            )

            self._cache[key] = entry
            self._stats.total_entries = len(self._cache)

            logger.debug(f"Cache set: {key[:8]}... (ttl: {ttl}s)")

    async def invalidate(
        self,
        prompt: str,
        task_type: Optional[str] = None,
        quality_threshold: Optional[float] = None,
        cost_limit: Optional[float] = None
    ) -> bool:
        """
        Invalidate a specific cache entry.

        Args:
            prompt: The request prompt
            task_type: Optional task type
            quality_threshold: Optional quality threshold
            cost_limit: Optional cost limit

        Returns:
            True if entry was found and removed
        """
        key = self._generate_key(prompt, task_type, quality_threshold, cost_limit)

        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats.total_entries = len(self._cache)
                logger.debug(f"Cache invalidated: {key[:8]}...")
                return True
            return False

    async def invalidate_by_task_type(self, task_type: str) -> int:
        """
        Invalidate all entries for a specific task type.

        Args:
            task_type: Task type to invalidate

        Returns:
            Number of entries removed
        """
        async with self._lock:
            keys_to_remove = [
                key for key, entry in self._cache.items()
                if entry.task_type == task_type
            ]

            for key in keys_to_remove:
                del self._cache[key]

            self._stats.total_entries = len(self._cache)

            if keys_to_remove:
                logger.info(f"Invalidated {len(keys_to_remove)} entries for task type: {task_type}")

            return len(keys_to_remove)

    async def invalidate_by_model(self, model_name: str) -> int:
        """
        Invalidate all entries that used a specific model.

        Useful when a model is updated or known to have issues.

        Args:
            model_name: Model name to invalidate

        Returns:
            Number of entries removed
        """
        async with self._lock:
            keys_to_remove = [
                key for key, entry in self._cache.items()
                if model_name in entry.models_used
            ]

            for key in keys_to_remove:
                del self._cache[key]

            self._stats.total_entries = len(self._cache)

            if keys_to_remove:
                logger.info(f"Invalidated {len(keys_to_remove)} entries for model: {model_name}")

            return len(keys_to_remove)

    async def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._stats.total_entries = 0
            logger.info(f"Cache cleared: {count} entries removed")
            return count

    async def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        async with self._lock:
            now = time.time()
            keys_to_remove = [
                key for key, entry in self._cache.items()
                if entry.expires_at < now
            ]

            for key in keys_to_remove:
                del self._cache[key]
                self._stats.expired_removals += 1

            self._stats.total_entries = len(self._cache)

            if keys_to_remove:
                logger.debug(f"Cleanup removed {len(keys_to_remove)} expired entries")

            return len(keys_to_remove)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "hits": self._stats.hits,
            "misses": self._stats.misses,
            "hit_rate": f"{self._stats.hit_rate:.2f}%",
            "evictions": self._stats.evictions,
            "expired_removals": self._stats.expired_removals,
            "total_entries": self._stats.total_entries,
            "max_size": self.max_size,
            "default_ttl_seconds": self.default_ttl
        }

    async def start_cleanup_task(self) -> None:
        """Start background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Cache cleanup task started")

    async def stop_cleanup_task(self) -> None:
        """Stop background cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("Cache cleanup task stopped")

    async def _cleanup_loop(self) -> None:
        """Background loop for periodic cleanup."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")


class SemanticCache(ResponseCache):
    """
    Extended cache with semantic similarity matching.

    Falls back to exact matching if no similarity function provided.
    This is a placeholder for future semantic caching capabilities.
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl_seconds: float = 3600.0,
        similarity_threshold: float = 0.95
    ):
        """
        Initialize semantic cache.

        Args:
            max_size: Maximum number of entries
            default_ttl_seconds: Default TTL
            similarity_threshold: Minimum similarity for cache hit (0-1)
        """
        super().__init__(max_size, default_ttl_seconds)
        self.similarity_threshold = similarity_threshold
        # Placeholder for embedding function
        self._embedding_func = None

    def set_embedding_function(self, func) -> None:
        """
        Set the embedding function for semantic similarity.

        Args:
            func: Async function that takes text and returns embedding vector
        """
        self._embedding_func = func

    # Note: Full semantic matching would require storing embeddings
    # and computing similarities. This is a placeholder for future enhancement.


# Convenience function for creating configured cache
def create_cache(
    cache_type: str = "lru",
    max_size: int = 1000,
    ttl_seconds: float = 3600.0,
    **kwargs
) -> ResponseCache:
    """
    Factory function to create cache instances.

    Args:
        cache_type: Type of cache ("lru" or "semantic")
        max_size: Maximum cache size
        ttl_seconds: Default TTL
        **kwargs: Additional cache-specific arguments

    Returns:
        Configured cache instance
    """
    if cache_type == "semantic":
        return SemanticCache(
            max_size=max_size,
            default_ttl_seconds=ttl_seconds,
            similarity_threshold=kwargs.get("similarity_threshold", 0.95)
        )
    else:
        return ResponseCache(
            max_size=max_size,
            default_ttl_seconds=ttl_seconds,
            cleanup_interval_seconds=kwargs.get("cleanup_interval", 300.0)
        )
