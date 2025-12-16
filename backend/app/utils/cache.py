# Caching utilities - to be filled from cache_py.txt
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheManager:
    """Cache manager with Redis support and in-memory fallback."""

    def __init__(
        self,
        enabled: bool = False,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        ttl: int = 86400
    ):
        """
        Initialize cache manager.

        Args:
            enabled: Enable Redis caching
            redis_host: Redis server host
            redis_port: Redis server port
            redis_db: Redis database number
            ttl: Cache TTL in seconds
        """
        self.enabled = enabled
        self.ttl = ttl
        self.redis_client = None
        self.in_memory_cache: Dict[str, Dict[str, Any]] = {}

        if enabled:
            try:
                import redis
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True
                )
                self.redis_client.ping()
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis: {e}. Using in-memory cache.")
                self.enabled = False

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    logger.debug(f"Cache hit: {key}")
                    return json.loads(value)
            except Exception as e:
                logger.warning(f"Redis get error: {e}")

        # In-memory fallback
        if key in self.in_memory_cache:
            entry = self.in_memory_cache[key]
            if entry["expires_at"] > datetime.utcnow():
                logger.debug(f"In-memory cache hit: {key}")
                return entry["value"]
            else:
                del self.in_memory_cache[key]

        return None

    def set(
        self,
        key: str,
        value: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL override

        Returns:
            True if successful
        """
        ttl = ttl or self.ttl

        if self.redis_client:
            try:
                self.redis_client.setex(
                    key,
                    ttl,
                    json.dumps(value)
                )
                logger.debug(f"Redis cache set: {key}")
                return True
            except Exception as e:
                logger.warning(f"Redis set error: {e}")

        # In-memory fallback
        self.in_memory_cache[key] = {
            "value": value,
            "expires_at": datetime.utcnow() + timedelta(seconds=ttl)
        }
        logger.debug(f"In-memory cache set: {key}")
        return True

    def delete(self, key: str) -> bool:
        """Delete cache entry."""
        if self.redis_client:
            try:
                self.redis_client.delete(key)
                return True
            except Exception as e:
                logger.warning(f"Redis delete error: {e}")

        if key in self.in_memory_cache:
            del self.in_memory_cache[key]
            return True

        return False

    def clear_all(self) -> bool:
        """Clear entire cache."""
        if self.redis_client:
            try:
                self.redis_client.flushdb()
                logger.info("Redis cache cleared")
                return True
            except Exception as e:
                logger.warning(f"Redis clear error: {e}")

        self.in_memory_cache.clear()
        logger.info("In-memory cache cleared")
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if self.redis_client:
            try:
                info = self.redis_client.info()
                return {
                    "type": "redis",
                    "keys": info.get("db0", {}).get("keys", 0),
                    "memory_usage": info.get("used_memory_human", "N/A")
                }
            except Exception as e:
                logger.warning(f"Error getting Redis stats: {e}")

        return {
            "type": "in-memory",
            "keys": len(self.in_memory_cache),
            "memory_usage": "N/A"
        }