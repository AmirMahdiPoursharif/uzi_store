from django.contrib import admin

from .models import Order, OrderItem, InventoryReservation


# Register your models here.

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    pass


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    pass


@admin.register(InventoryReservation)
class InventoryReservationAdmin(admin.ModelAdmin):
    pass
