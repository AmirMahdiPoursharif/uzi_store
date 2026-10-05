from django.contrib import admin

from product.models import Product, ProductImage, Category, Review, Reply

# Django Admin Registrations

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Configuration for managing Product models in the Django admin interface."""
    list_display = ("name", "parent", "variant_name", "category",)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    """Configuration for managing Product Image galleries in the Django admin interface."""
    list_display = ("product", "picture",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Configuration for managing Categories in the Django admin interface."""
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Configuration for managing Reviews in the Django admin interface."""
    list_display = ("product", "user", "rating")


@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    """Configuration for managing Replies in the Django admin interface."""
    list_display = ("review", "user",)
