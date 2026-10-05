from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from product.models import Product, Review

@receiver([post_save, post_delete], sender=Product)
@receiver([post_save, post_delete], sender=Review)
def invalidate_products_cache(sender, instance, **kwargs):
    """
    Listens for Product creation, updates, or deletions.
    Increments the global 'products_cache_version' to effectively 
    invalidate stale cached product queries.
    """
    cache_key = "products_cache_version"

    # Retrieve current version (default to 1) and increment
    current_cache_version = cache.get(cache_key, 1)
    new_cache_version = current_cache_version + 1

    # Persist the new cache version permanently
    cache.set(cache_key, new_cache_version, timeout=None)
