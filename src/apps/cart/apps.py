from django.apps import AppConfig


class CartAppConfig(AppConfig):
    """Configuration class for the cart application."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cart'
    label = 'cart_app'

    def ready(self):
        """
        Override the ready method to explicitly import and register 
        application signals (like automatic cart creation) on startup.
        """
