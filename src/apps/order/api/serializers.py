from rest_framework import serializers

from order import models
from product.models import Product
from order.models import OrderStatus


class OrderProductSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = ("category", "name")


class OrderItemSerializer(serializers.ModelSerializer):
    product = OrderProductSerializer(read_only=True)

    class Meta:
        model = models.OrderItem
        fields = ["product", "price", "quantity"]
        read_only_fields = ("price", "quantity", "description", "name")

class OrderSerializer(serializers.ModelSerializer):
    payment_url = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = models.Order
        fields = "__all__"
        read_only_fields = ("order_id", "user", "created_at", "transaction_id", "status", "total_price")

    def get_payment_url(self, obj):
        if obj.status == OrderStatus.PENDING_PAYMENT:
            request = self.context.get("request")
            return request.build_absolute_uri(f"order/payment/{obj.order_id}")
        return None

class OrderDetailSerializer(OrderSerializer):
    order_items = OrderItemSerializer(many=True, read_only=True)


class ManagerPanelSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source="user.phone", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = models.Order
        fields = ["order_id", "total_price", "phone", "email", "shipping_cost", "status", "transaction_id"]

class ManagerPanelDetailSerializer(ManagerPanelSerializer):
    order_details = serializers.HyperlinkedIdentityField(
        view_name="manager-order-detail",
        read_only=True
    )
