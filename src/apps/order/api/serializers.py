from rest_framework import serializers

from order import models
from product.models import Product
from order.models import OrderStatus


class OrderProductSerializer(serializers.ModelSerializer):
    # هر قلم سفارش فقط نام محصول و دسته را از اطلاعات فعلی محصول نمایش می‌دهد.
    category = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = ("category", "name")


class OrderItemSerializer(serializers.ModelSerializer):
    # قیمت و تعداد از خود قلم سفارش خوانده می‌شوند و با تغییر محصول بازنویسی نمی‌شوند.
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
        # ساخت لینک برای سفارش معلق به request موجود در context نیاز دارد.
        if obj.status == OrderStatus.PENDING_PAYMENT:
            request = self.context.get("request")
            return request.build_absolute_uri(f"order/payment/{obj.order_id}")
        return None

class OrderDetailSerializer(OrderSerializer):
    # جزئیات، همان فیلدهای خلاصه سفارش را به همراه اقلام تو در تو برمی‌گرداند.
    order_items = OrderItemSerializer(many=True, read_only=True)


class ManagerPanelSerializer(serializers.ModelSerializer):
    # اطلاعات تماس از کاربر مرتبط خوانده می‌شود تا در فهرست مدیریتی همراه سفارش باشد.
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
