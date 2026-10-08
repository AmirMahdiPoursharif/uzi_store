import uuid

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.utils.text import slugify
from order.models import InventoryReservation, OrderStatus, OrderItem
from .utils import product_images_path


class Category(models.Model):
    """
    Represents a product category. Automatically generates a URL-friendly slug 
    based on the category name upon saving.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        # Generate or update the slug if it's empty or if the name has changed
        if not self.slug or (self.pk and self.name != self.__class__.objects.get(pk=self.pk).name):
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Core product model storing details, pricing, and overall stock.
    Uses a UUID for secure, unguessable public identification.
    """
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    show = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Self-referencing foreign key to support product variants (e.g., colors, memory).
    # If this field is null, the record represents a base (parent) product.
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="variants")
    
    # Stores the specific attributes of a child variant (e.g., "Black - 256GB").
    # Should be left blank for base (parent) products.
    variant_name = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ["name", "parent", "variant_name"]

    def clean(self):
        """
        Validates product hierarchy to prevent self-parenting, 
        multi-level nesting, and duplicate variant creations.
        """
        # ساختار مجاز یک محصول پایه و گونه‌های مستقیم آن است؛ سطح سوم پذیرفته نمی‌شود.
        if self.parent:
            if self.pk and self.parent.pk == self.pk:
                raise ValidationError(
                    {"parent": "A product cannot be its own parent"}
                )

            if self.parent.parent is not None:
                raise ValidationError(
                    {"parent": "A variant cannot be assigned as a parent. Parents must be base products"}
                )
            
            if self.pk and self.variants.exists():
                raise ValidationError(
                    {"parent": "A product that already has variants cannot become a variant of another product"}
                )
            
        # کنترل تکراری بودن، رکورد جاری را هنگام ویرایش از جست‌وجو کنار می‌گذارد.
        qs = Product.objects.filter(
            name=self.name, parent=self.parent, variant_name=self.variant_name)
             
        if self.pk:
            qs = qs.exclude(pk=self.pk)

        if qs.exists():
            raise ValidationError(
                "A product with this exact name, parent, and variant already exists"
            )
        
        if self.parent is not None and (not self.variant_name or self.variant_name.strip() == ""):
            raise ValidationError(
                {"variant_name": "If a product has a parent, it must provide a variant name"}
            )
            
        super().clean()

    def save(self, *args, **kwargs):
        """Ensures full validation rules are executed before saving to the database."""
        self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        """
        Returns the variant name alongside the parent's name if it's a child product,
        otherwise returns the base product's name.
        """
        if self.parent:
            return f"{self.name} ({self.variant_name}) variant of *{self.parent.name}* "
        
        return self.name

    def available_stock(self):
        """
        Calculates the actual available stock by subtracting quantities 
        held in active, unpaid inventory reservations from the total stock.
        """
        # ملاک این محاسبه، وضعیت و مهلت سفارش است؛ فیلد status خود رزرو فیلتر نمی‌شود.
        # رزرو سفارش منقضی‌شده حتی پیش از اجرای پاک‌سازی از جمع کنار می‌رود.
        active_reservations = (
                InventoryReservation.objects.filter(
                    product=self,
                    order__status=OrderStatus.PENDING_PAYMENT,
                    order__expires_at__gt=timezone.now()
                ).aggregate(
                    total=Sum("quantity")
                )["total"] or 0
        )
        return self.stock - active_reservations


class ProductImage(models.Model):
    """Handles multiple images associated with a single product."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    picture = models.ImageField(upload_to=product_images_path)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # سقف ده تصویر فقط هنگام ایجاد رکورد تصویر جدید بررسی می‌شود.
        if self.pk is None:
            existing_images_count = ProductImage.objects.filter(product=self.product).count()
            if existing_images_count >= 10:
                raise ValidationError("Maximum 10 images are allowed per product")
        return super().clean()
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"picture for ** {self.product.name} **"


class Review(models.Model):
    """
    User reviews for products. Enforces a 1-to-5 rating scale 
    and ensures a user can only review a specific product once.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    description = models.TextField()
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        # Prevent multiple reviews by the same user
        unique_together = ["product", "user"]

    def __str__(self):
        return f"Review by {self.user.full_name} for {self.product.name} ({self.rating})"
    

class Reply(models.Model):
    """User or admin replies to existing product reviews."""
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="replies")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="replies")
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Reply by {self.user.full_name} to {self.review}"
