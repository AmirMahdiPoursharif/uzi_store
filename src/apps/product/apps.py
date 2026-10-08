from django.apps import AppConfig


class ProductsAppConfig(AppConfig):
    """
    Application configuration for the 'products_app'.
    Handles initialization tasks on startup.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'product'
    # نام ماژول product است؛ برچسب قدیمی برای سازگاری با روابط و migrationها حفظ شده است.
    label = 'products_app'

    def ready(self):
        """
        Override the ready method to import and register signal handlers
        ensuring they are connected when the Django application starts.
        """
        # Imported for its @receiver side effect, so it reads as unused (F401).
        # Without the noqa, `ruff check --fix` deletes this line and the product
        # cache-version signals stop firing.
        import product.signals  # noqa: F401
