from rest_framework import serializers

from cart.models import Cart, CartItem
from product.api.serializers import ProductSerializer
from product.models import Product


class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializes individual items within a cart. 
    Accepts a product UUID for write operations, but returns full product details on read.
    """
    product = ProductSerializer(read_only=True)

    # Write-only field to accept UUID from the client and resolve it to a Product instance
    product_uuid = serializers.SlugRelatedField(queryset=Product.objects.all(), slug_field="uuid",
                                                source="product", write_only=True)

    # Dynamically calculated field for the line-item cost
    total_cost = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_uuid", "quantity", "total_cost"]

    def get_total_cost(self, obj):
        """Fetches the calculated cost for this item (price * quantity)."""
        return obj.get_cost()


class CartSerializer(serializers.ModelSerializer):
    """Serializes the entire cart, including nested items and the overall total cost."""
    user = serializers.ReadOnlyField(source="user.email")
    items = CartItemSerializer(many=True, read_only=True)
    total_cost = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "user", "items", "total_cost", "created_at"]
        read_only_fields = ["id", "user", "created_at"]

    def get_total_cost(self, obj):
        """Fetches the aggregated total cost of the cart."""
        return obj.get_total_cost()
