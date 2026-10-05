import logging

from django.core.cache import caches
from django.core.cache.backends.base import BaseCache

logger = logging.getLogger(__name__)


class FallbackCache(BaseCache):
    """
    A custom cache backend that implements a primary/fallback mechanism.
    If the primary cache (e.g., Redis) fails, it falls back to the secondary
    cache (e.g., local memory) for reads, and performs dual-writes for consistency.
    """
    def __init__(self, name, params):
        super().__init__(params)
        self.primary_cache_name = params.get('PRIMARY', 'redis')
        self.fallback_cache_name = params.get('FALLBACK', 'local')

    @property
    def primary(self):
        return caches[self.primary_cache_name]

    @property
    def fallback(self):
        return caches[self.fallback_cache_name]

    def get(self, key, default=None, version=None):
        """Attempts to read from the primary cache, falling back on failure."""
        try:
            result = self.primary.get(key, default, version=version)
            return result

        except Exception as e:
            logger.warning(f"Primary cache ({self.primary_cache_name}) failed in get: {e}")

            try:
                # Fallback attempt
                result = self.fallback.get(key, default, version=version)
                logger.info(f"Successfully retrieved key from fallback cache ({self.fallback_cache_name})")
                return result

            except Exception as e:
                # Both caches failed
                logger.critical(f"Both primary and fallback caches failed in get: {e}")
                return default

    def set(self, key, value, timeout=None, version=None):
        """Performs a dual-write to both primary and fallback caches."""
        try:
            self.primary.set(key, value, timeout=timeout, version=version)
        except Exception as e:
            logger.warning(f"Failed to write to primary cache: {e}")

        try:
            self.fallback.set(key, value, timeout=timeout, version=version)
        except Exception as e:
            logger.warning(f"Failed to write to fallback cache: {e}")

    def delete(self, key, version=None):
        """Deletes the key from both caches to maintain consistency."""
        try:
            self.primary.delete(key, version=version)
        except Exception as e:
            logger.warning(f"Failed to delete from primary cache: {e}")

        try:
            self.fallback.delete(key, version=version)
        except Exception as e:
            logger.warning(f"Failed to delete from fallback cache: {e}")

    def has_key(self, key, version=None):
        """Checks existence in the primary cache, then checks fallback if needed."""
        try:
            return self.primary.has_key(key, version=version)
        except Exception:
            try:
                return self.fallback.has_key(key, version=version)
            except Exception:
                return False

    def clear(self):
        """Clears both primary and fallback caches."""
        try:
            self.primary.clear()
        except Exception as e:
            logger.warning(f"Primary cache clearing failed: {e}")
        try:
            self.fallback.clear()
        except Exception as e:
            logger.warning(f"Fallback cache clearing failed: {e}")
