from django.contrib import admin

from cart.models import Cart, CartItem


# Register your models here.

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Registers the Cart model in the Django admin interface."""
    list_display = ("user",)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Registers the CartItem model in the Django admin interface."""
    list_display = ("cart", "product", "quantity",)
