from django.apps import AppConfig


class ProductsAppConfig(AppConfig):
    """
    Application configuration for the 'products_app'.
    Handles initialization tasks on startup.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'product'
    label = 'products_app'

    def ready(self):
        """
        Override the ready method to import and register signal handlers
        ensuring they are connected when the Django application starts.
        """
        import product.signals
