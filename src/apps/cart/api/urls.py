from django.urls import path

from cart.api import views

# مسیر خالی در این فایل همان cart/ است و جزئیات سبد کاربر جاری را نمایش می‌دهد.
urlpatterns = [
    # API endpoints for managing the user's shopping cart
    path("", views.CartDetailView.as_view(), name="cart_detail"),
    path("addItem/", views.CartAddItemView.as_view(), name="cart_add_item"),
    path("removeItem/", views.CartRemoveItemView.as_view(), name="cart_remove_item"),
]
