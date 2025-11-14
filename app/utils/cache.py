"""Redis caching utility for responses"""

import hashlib
import json
import logging
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class CacheClient:
    """Redis cache client for caching LLM responses"""

    def __init__(self, redis_url: str, enabled: bool = True):
        """
        Initialize Redis cache client

        Args:
            redis_url: Redis connection URL
            enabled: Whether caching is enabled
        """
        self.enabled = enabled
        self.redis_url = redis_url
        self._client = None

        if self.enabled:
            try:
                self._client = Redis.from_url(redis_url, decode_responses=True)
                # Test connection
                self._client.ping()
                logger.info(f"Connected to Redis cache at {redis_url}")
            except RedisError as e:
                logger.warning(f"Failed to connect to Redis: {e}. Caching disabled.")
                self.enabled = False
                self._client = None

    def _generate_key(self, prefix: str, data: dict) -> str:
        """
        Generate a cache key from data

        Args:
            prefix: Key prefix (e.g., 'embedding', 'inference')
            data: Data to hash

        Returns:
            Cache key string
        """
        # Sort dict for consistent hashing
        data_str = json.dumps(data, sort_keys=True)
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()[:16]
        return f"{prefix}:{data_hash}"

    def get(self, prefix: str, data: dict) -> Any | None:
        """
        Get cached value

        Args:
            prefix: Cache key prefix
            data: Request data to generate key

        Returns:
            Cached value or None if not found
        """
        if not self.enabled or not self._client:
            return None

        try:
            key = self._generate_key(prefix, data)
            value = self._client.get(key)

            if value:
                logger.debug(f"Cache hit for key: {key}")
                return json.loads(value)
            else:
                logger.debug(f"Cache miss for key: {key}")
                return None

        except RedisError as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(self, prefix: str, data: dict, value: Any, ttl: int = 3600) -> bool:
        """
        Set cached value

        Args:
            prefix: Cache key prefix
            data: Request data to generate key
            value: Value to cache
            ttl: Time to live in seconds

        Returns:
            True if successful
        """
        if not self.enabled or not self._client:
            return False

        try:
            key = self._generate_key(prefix, data)
            value_json = json.dumps(value)
            self._client.setex(key, ttl, value_json)
            logger.debug(f"Cached value for key: {key} (TTL: {ttl}s)")
            return True

        except RedisError as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, prefix: str, data: dict) -> bool:
        """
        Delete cached value

        Args:
            prefix: Cache key prefix
            data: Request data to generate key

        Returns:
            True if successful
        """
        if not self.enabled or not self._client:
            return False

        try:
            key = self._generate_key(prefix, data)
            self._client.delete(key)
            logger.debug(f"Deleted cache key: {key}")
            return True

        except RedisError as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def clear_prefix(self, prefix: str) -> int:
        """
        Clear all keys with a given prefix

        Args:
            prefix: Prefix to clear

        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self._client:
            return 0

        try:
            pattern = f"{prefix}:*"
            keys = list(self._client.scan_iter(match=pattern))
            if keys:
                deleted = self._client.delete(*keys)
                logger.info(f"Cleared {deleted} keys with prefix: {prefix}")
                return deleted
            return 0

        except RedisError as e:
            logger.error(f"Cache clear error: {e}")
            return 0

    def clear_all(self) -> bool:
        """
        Clear all cache entries

        Returns:
            True if successful
        """
        if not self.enabled or not self._client:
            return False

        try:
            self._client.flushdb()
            logger.info("Cleared all cache entries")
            return True

        except RedisError as e:
            logger.error(f"Cache flush error: {e}")
            return False

    def get_stats(self) -> dict:
        """
        Get cache statistics

        Returns:
            Dictionary with cache stats
        """
        if not self.enabled or not self._client:
            return {"enabled": False, "status": "disabled"}

        try:
            info = self._client.info("stats")
            memory_info = self._client.info("memory")

            return {
                "enabled": True,
                "status": "connected",
                "total_keys": self._client.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0), info.get("keyspace_misses", 0)
                ),
                "memory_used_mb": round(memory_info.get("used_memory", 0) / 1024 / 1024, 2),
                "memory_peak_mb": round(memory_info.get("used_memory_peak", 0) / 1024 / 1024, 2),
            }

        except RedisError as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"enabled": True, "status": "error", "error": str(e)}

    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)

    def close(self):
        """Close Redis connection"""
        if self._client:
            self._client.close()
            logger.info("Closed Redis connection")


# Global cache instance (initialized when needed)
_cache_client: CacheClient | None = None


def get_cache_client(redis_url: str, enabled: bool = True) -> CacheClient:
    """Get or create cache client instance"""
    global _cache_client
    if _cache_client is None:
        _cache_client = CacheClient(redis_url, enabled)
    return _cache_client
