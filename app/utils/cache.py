"""Redis caching utility for responses"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, Optional, TypeVar, cast

from redis import Redis
from redis.exceptions import RedisError

# Define a proper type variable for response types
T = TypeVar("T")
ResponseT = TypeVar("ResponseT")

logger = logging.getLogger(__name__)


class CacheClient:
    """Redis cache client for caching LLM responses"""

    def __init__(self, redis_url: str, enabled: bool = True) -> None:
        """
        Initialize Redis cache client

        Args:
            redis_url: Redis connection URL
            enabled: Whether caching is enabled
        """
        self.enabled = enabled
        self.redis_url = redis_url
        self._client: Optional[Redis] = None  # type: ignore[valid-type]

        if self.enabled:
            try:
                self._client = Redis.from_url(redis_url, decode_responses=True)
                if self._client is None:
                    raise RedisError("client failed to initialize")

                self._client.ping()
                logger.info(f"Connected to Redis cache at {redis_url}")
            except RedisError as e:
                logger.warning(f"Failed to connect to Redis: {e}. Caching disabled.")
                self.enabled = False
                self._client = None

    def _generate_key(self, prefix: str, data: Dict[str, Any]) -> str:
        """
        Generate a cache key from data

        Args:
            prefix: Key prefix (e.g., 'embedding', 'inference')
            data: Data to hash

        Returns:
            Cache key string
        """
        data_str = json.dumps(data, sort_keys=True)
        key_hash = hashlib.md5(data_str.encode()).hexdigest()
        return f"{prefix}:{key_hash}"

    def get(self, prefix: str, data: Dict[str, Any]) -> Optional[Any]:
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
            if value is not None and isinstance(value, (str, bytes, bytearray)):
                logger.debug(f"Cache hit for key: {key}")
                return json.loads(value)
            logger.debug(f"Cache miss for key: {key}")
            return None

        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(
        self, prefix: str, data: Dict[str, Any], value: Any, ttl: int = 3600
    ) -> bool:
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
            self._client.setex(key, ttl, value_json)  # type: ignore[arg-type]
            logger.debug(f"Cached value for key: {key} (TTL: {ttl}s)")
            return True

        except (RedisError, TypeError) as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, prefix: str, data: Dict[str, Any]) -> bool:
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
            self._client.delete(key)  # type: ignore[attr-defined]
            logger.debug(f"Deleted cache key: {key}")
            return True

        except RedisError as e:
            logger.error(f"Cache delete error: {e}")
            return False

    async def clear_prefix(self, prefix: str) -> int:
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
            keys = await self._client.keys(f"{prefix}:*")
            if keys:
                str_keys = [
                    key.decode("utf-8") if isinstance(key, bytes) else key
                    for key in keys
                ]
                return cast(int, self._client.delete(*str_keys))  # type: ignore[attr-defined]
            return 0
        except (RedisError, AttributeError) as e:
            logger.error(f"Error clearing cache prefix {prefix}: {e}")
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
            self._client.flushdb()  # type: ignore[attr-defined]
            logger.info("Cleared all cache entries")
            return True

        except (RedisError, AttributeError) as e:
            logger.error(f"Cache flush error: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache stats
        """
        if not self.enabled or not self._client:
            return {
                "enabled": False,
                "keys": 0,
                "hits": 0,
                "misses": 0,
                "hit_rate": 0.0,
                "memory_usage": 0,
            }

        try:
            info = self._client.info()  # type: ignore[attr-defined]
            if not isinstance(info, dict):
                raise ValueError("Unexpected Redis info format")

            keyspace_hits = int(info.get("keyspace_hits", 0))
            keyspace_misses = int(info.get("keyspace_misses", 0))

            stats: Dict[str, Any] = {
                "enabled": True,
                "keys": int(self._client.dbsize()),  # type: ignore[attr-defined]
                "hits": keyspace_hits,
                "misses": keyspace_misses,
                "hit_rate": self._calculate_hit_rate(keyspace_hits, keyspace_misses),
                "memory_usage": int(info.get("used_memory", 0)),
            }
            return stats
        except (RedisError, ValueError, AttributeError) as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "enabled": False,
                "error": str(e),
            }

    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """
        Calculate cache hit rate

        Args:
            hits: Number of cache hits
            misses: Number of cache misses

        Returns:
            Hit rate as a percentage (0.0 to 100.0)
        """
        try:
            total = hits + misses
            if total == 0:
                return 0.0
            return round((hits / total) * 100, 2)
        except (TypeError, ZeroDivisionError):
            return 0.0

    def close(self) -> None:
        """Close Redis connection"""
        if self._client:
            self._client.close()  # type: ignore[attr-defined]
            logger.info("Closed Redis connection")


_cache_client: CacheClient | None = None


def get_cache_client(redis_url: str, enabled: bool = True) -> CacheClient:
    """Get or create cache client instance"""
    global _cache_client
    if _cache_client is None:
        _cache_client = CacheClient(redis_url, enabled)
    return _cache_client
