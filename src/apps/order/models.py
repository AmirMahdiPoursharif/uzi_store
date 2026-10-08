import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


# Create your models here.
class OrderStatus(models.IntegerChoices):
    # مقدار عددی در پایگاه داده ذخیره می‌شود و متن ترجمه‌پذیر برای نمایش است.
    PENDING_PAYMENT = 1, _('pending payment')
    PAID = 2, _('paid')
    PREPARING = 3, _('preparing')
    SENT = 4, _('sent')
    DELIVERED = 5, _('delivered')
    CANCELED = 6, _('canceled')
    EXPIRED = 7, _('expired')


class InventoryReservationStatus(models.IntegerChoices):
    RELEASED = 0, _('reservation is released')
    ACTIVE = 1, _('reservation is active')


class Order(models.Model):
    # order_id شناسه عمومی سفارش است و از کلید اصلی داخلی مدل جدا نگه داشته می‌شود.
    order_id = models.CharField(max_length=25, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total_price = models.PositiveIntegerField(default=0)
    shipping_cost = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(null=True, blank=True)
    status = models.IntegerField(choices=OrderStatus.choices, default=OrderStatus.PENDING_PAYMENT)
    created_at = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True, unique=True, editable=False)
    track_id = models.CharField(max_length=100, null=True, blank=True, unique=True, editable=False)

    def save(self, *args, **kwargs):
        # شناسه عمومی فقط در اولین ذخیره و در صورت خالی بودن ساخته می‌شود.
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.order_id:
            # generates an order number something like : ORD-2026523-000026
            date = timezone.now().strftime('%Y%m%d')

            while True:
                order_num = secrets.token_hex(3)
                if not Order.objects.filter(order_id=order_num).exists():
                    break

            self.order_id = f"Uzi-{date}-{order_num}"
            super().save(update_fields=["order_id"])

    def set_expires_at(self):
        # سفارش در انتظار پرداخت، از زمان اجرای این متد پانزده دقیقه مهلت می‌گیرد.
        if self.status == OrderStatus.PENDING_PAYMENT:
            self.expires_at = timezone.now() + timedelta(minutes=15)
            self.save(update_fields=["expires_at"])

    def is_expired(self):
        # این متد فقط زمان را بررسی می‌کند و وضعیت ذخیره‌شده سفارش را تغییر نمی‌دهد.
        return (
                self.status == OrderStatus.PENDING_PAYMENT
                and
                self.expires_at
                and
                self.expires_at < timezone.now()
        )

    def expire(self):
        # ثبت انقضا، رزروهای سفارش را نیز آزاد می‌کند تا دیگر فعال باقی نمانند.
        if self.status == OrderStatus.PENDING_PAYMENT:
            if self.is_expired():
                self.reservations.update(status=InventoryReservationStatus.RELEASED)
                self.status = OrderStatus.EXPIRED
                self.save(update_fields=["status"])

    def __str__(self):
        return f"{self.order_id}"

    def update_total_price(self):
        # جمع سفارش از قیمت ثبت‌شده اقلام و هزینه ارسال محاسبه می‌شود.
        total = 0
        for item in self.order_items.all():
            total += item.subtotal()
        total += self.shipping_cost

        self.total_price = total

        self.save(update_fields=["total_price", ])

    def get_order_items(self):
        order_items = OrderItem.objects.filter(order=self)
        if order_items.exists():
            return order_items
        else:
            return None


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    # ارجاع رشته‌ای به محصول مانع import حلقوی بین مدل‌های سفارش و محصول می‌شود.
    product = models.ForeignKey("products_app.Product", on_delete=models.CASCADE)
    # قیمت زمان ثبت سفارش حفظ می‌شود، حتی اگر قیمت محصول بعداً تغییر کند.
    price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()

    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product.name} for {self.order.order_id} with price {self.subtotal()}"


class InventoryReservation(models.Model):
    # رزرو، تعداد کنارگذاشته‌شده برای سفارش را بدون کاهش موجودی واقعی نگه می‌دارد.
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='reservations')
    product = models.ForeignKey("products_app.Product", on_delete=models.CASCADE, related_name='preservations')
    quantity = models.PositiveIntegerField()
    status = models.IntegerField(choices=InventoryReservationStatus.choices, default=InventoryReservationStatus.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity}x {self.product.name} reservation with status {self.status} for {self.order.order_id}"
