from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from cart.models import Cart


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_cart(sender, instance, created, **kwargs):
    """
    Listens for the creation of a new User model.
    Automatically provisions an empty Cart tied to the user immediately after registration.
    """
    if created:
        Cart.objects.create(user=instance)
