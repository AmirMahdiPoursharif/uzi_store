from django.contrib import admin

from .models import Order, OrderItem, InventoryReservation


# Register your models here.

# سفارش، اقلام و رزروها با فرم‌های پیش‌فرض مدیریت Django ثبت می‌شوند.
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    pass


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    pass


@admin.register(InventoryReservation)
class InventoryReservationAdmin(admin.ModelAdmin):
    pass
