from django.urls import path

from order.api import views

# مسیرهای پنل سفارش زیر پیشوند manager/ در تنظیمات اصلی URL نصب می‌شوند.
urlpatterns = [
    path("panel/", views.ManagerPanelView.as_view(), name="manager-panel"),
    path("order/<str:order_id>", views.ManagerOrderPanelView.as_view(), name="manager-order-detail")
]
