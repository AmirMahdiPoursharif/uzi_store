from django.conf import settings
from django.db import models

from product.models import Product


# Create your models here.

class Cart(models.Model):
    """
    Represents a user's shopping cart. 
    Strictly linked to a single user via a One-to-One relationship.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"cart of {self.user.email}"

    def get_total_cost(self):
        """Calculates and returns the total monetary value of all items in the cart."""
        return sum(item.get_cost() for item in self.items.all())

    def get_cart_items(self):
        """
        Retrieves all items associated with this cart. 
        Returns None if the cart is completely empty.
        """
        cart_items = CartItem.objects.filter(cart=self)
        if cart_items.exists():
            return cart_items
        else:
            return None


class CartItem(models.Model):
    """Represents a specific product and its chosen quantity inside a cart."""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity}x {self.product.name} in {self.cart}"

    def get_cost(self):
        """Calculates the total cost for this specific item line (price * quantity)."""
        # مبلغ سبد با قیمت فعلی محصول محاسبه می‌شود؛ تثبیت قیمت هنگام ایجاد سفارش است.
        return self.product.price * self.quantity
