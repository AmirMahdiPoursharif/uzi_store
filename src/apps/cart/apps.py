from django.apps import AppConfig


class CartAppConfig(AppConfig):
    """Configuration class for the cart application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "cart"
    # نام جدول‌های قبلی به این برچسب وابسته است، نه به نام پوشه cart.
    label = "cart_app"

    def ready(self):
        """
        Override the ready method to explicitly import and register
        application signals (like automatic cart creation) on startup.
        """
        # Imported for its @receiver side effect, so it reads as unused (F401).
        # Without the noqa, `ruff check --fix` deletes this line and carts stop
        # being auto-created.
        import cart.signals  # noqa: F401
