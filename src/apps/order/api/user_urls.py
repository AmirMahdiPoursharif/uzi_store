from django.urls import path

from order.api import views

urlpatterns = [
    # مسیرهای ثابت باید پیش از الگوی عمومی order_id قرار بگیرند.
    path("", views.OrderList.as_view(), name="orders"),
    path("create/", views.OrderCreate.as_view(), name="order_create"),
    path("payment/callback/", views.Callback.as_view(), name="callback"),
    path("payment/<str:order_id>/", views.Payment.as_view(), name="payment"),
    path("<str:order_id>/", views.OrderDetail.as_view(), name="order_detail"),
]
