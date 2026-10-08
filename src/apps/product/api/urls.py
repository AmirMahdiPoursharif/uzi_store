from django.urls import path
from product.api import views

# این مجموعه مستقیماً در ریشه URLها نصب شده و پیشوند هر مسیر در همین‌جا آمده است.
urlpatterns = [
    # Public & User Endpoints (Products & Categories)
    path("user/products/", views.UserProductListView.as_view(), name="user_product_list"),
    path("user/product/<uuid:uuid>/", views.UserProductDetailView.as_view(), name="user_product_detail"),
    path("user/categories/", views.UserCategoryListView.as_view(), name="user_category_list"),
    path("user/category/<slug:category_slug>/", views.UserCategoryDetailView.as_view(), name="user_category_detail"),

    # Admin Endpoints (Requires Superuser Privileges)
    path("api/admin/products/", views.AdminProductListView.as_view(), name="admin_product_list"),
    path("api/admin/product/<uuid:uuid>/", views.AdminProductDetailView.as_view(), name="admin_product_detail"),
    path("api/admin/categories/", views.AdminCategoryListView.as_view(), name="admin_category_list"),
    path("api/admin/category/<slug:category_slug>/", views.AdminCategoryDetailView.as_view(), name="admin_category_detail"),

    # Review & Reply Management Endpoints
    path("products/<uuid:uuid>/reviews/", views.ProductReviewListView.as_view(), name="product_reviews"),
    path("reviews/<int:review_id>/", views.ReviewDetailView.as_view(), name="review_detail"),
    path("reviews/<int:review_id>/replies/", views.ReviewReplyListView.as_view(), name="review_replies"),
    path("replies/<int:reply_id>/", views.ReplyDetailView.as_view(), name="reply_detail"),
]
