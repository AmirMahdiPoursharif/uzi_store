import uuid

from rest_framework.exceptions import ValidationError


def product_images_path(instance, filename):
    """
    Generates a unique, structured file path for uploaded product images.
    Organizes files into directories based on category and product name, 
    and renames the file using a UUID to prevent filename collisions.
    """
    # Define explicitly allowed image formats
    accepted_types = ("png", "jpg", "jpeg", "webp",)
    # Extract the file extension
    # بررسی فعلی بر پسوند نام فایل متکی است و بزرگی یا کوچکی حروف را یکسان نمی‌کند.
    fmt = filename.split('.')[-1]
    if fmt in accepted_types:
        # Generate a unique filename while preserving the valid extension
        new_filename = f"{uuid.uuid4()}.{fmt}"
        return f"products/{instance.product.category.name}/{instance.product.name}/{new_filename}"
    else:
        # Reject unsupported file formats securely
        return ValidationError("invalid file format")
