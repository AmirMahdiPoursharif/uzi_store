import re
from django.db.models import Avg
from rest_framework import serializers
from product.models import Category, Product, Review, Reply

# Regex patterns for content moderation
phone_regex = r'(\+98|0)?9\d{9}'
email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

# Profanity filter list
banned_word = [
    "ass", "bitch", "fucker", "asshole", "idiot", "dumb", "dick", "pussy", "shet", "fuck", "motherfucker",
    "holy shet", "fuck you", "eat my ass", "dick face", "tit", "boob", "asswibe", "porn", "sex", "cock",
    "cock sucker", "sucker", "suck", "cum", "لا پایی", "کونده", "کله کیری", "سیکیم", "سوخوم", "قهبه", "سیهتیر",
    "حرومزاده", "کصکش", "جنده", "خارکصه", "کونی", "کیری", "مادرجنده", "مادرقهبه", "حرومی", "بی ناموس", "کص",
    "کیر", "کون", "ممه", "ننه جنده", "ننه قهبه", "ننه صلواتی", "کیر خر", "کسکش", "مادر کصه", "زن جنده"
]


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializes category data, exposing the URL-friendly slug 
    for frontend routing and filtering.
    """
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]
        read_only_fields = ["id", "slug"]


class ProductVariantSerializer(serializers.ModelSerializer):
    """
    Serializes specific product variants (children) to be nested 
    within their parent product's detailed response.
    """
    class Meta:
        model = Product
        fields = ["uuid", "name", "variant_name", "price", "available_stock"]


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializes comprehensive product data, including nested category details,
    aggregated ratings, and a preview of recent reviews.
    """
    # Embeds all related child variants into the parent product's response
    variants = ProductVariantSerializer(many=True, read_only=True)

    category = CategorySerializer(read_only=True)

    # Allows assigning a category via its slug during creation/update
    category_slug = serializers.SlugRelatedField(
        queryset=Category.objects.all(), slug_field="slug", write_only=True, source="category")
    
    # UUID ورودی به شیء والد تبدیل می‌شود؛ null به معنی محصول پایه است.
    parent_uuid = serializers.SlugRelatedField(
        queryset=Product.objects.all(), slug_field="uuid", source="parent", allow_null=True)
    
    review_count = serializers.IntegerField(read_only=True)
    avg_rating = serializers.SerializerMethodField()
    recent_reviews = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["uuid", "category", "category_slug", "name", "description",
                "price", "review_count", "avg_rating", "stock", "available_stock",
                 "recent_reviews", "variants", "parent_uuid", "variant_name"]
        read_only_fields = ["uuid"]

    def get_avg_rating(self, obj):
        """Calculates and returns the average user rating for the product."""
        # اگر view میانگین را annotate کرده باشد، از همان مقدار بدون پرس‌وجوی تازه استفاده می‌شود.
        if hasattr(obj, "avg_rating"):
            return obj.avg_rating if obj.avg_rating is not None else 0
        return obj.reviews.aggregate(Avg("rating"))["rating__avg"] or 0

    def get_recent_reviews(self, obj):
        """Fetches the 3 most recent reviews to display on the product detail page."""
        recent = obj.reviews.order_by("-created_at")[:3]
        return ReviewSerializer(recent, many=True).data
    
    def validate(self, data):
        """
        Enforces strict 1-level hierarchy for product variants.
        Prevents infinite loops and multi-level nesting.
        """
        validated_data = super().validate(data)
        parent = validated_data.get("parent")
        instance = self.instance
        # در PATCH، فیلدهای ارسال‌نشده از نمونه فعلی خوانده می‌شوند تا اعتبارسنجی کامل بماند.
        name = validated_data.get("name", getattr(instance, "name", None))
        parent = validated_data.get("parent", getattr(instance, "parent", None))
        variant_name = validated_data.get("variant_name", getattr(instance, "variant_name", None))

        if parent:
            if instance and parent.uuid == instance.uuid:
                raise serializers.ValidationError(
                    {"parent_uuid": "A product cannot be its own parent"}
                )

            if parent.parent is not None:
                raise serializers.ValidationError(
                    {"parent_uuid": "A variant cannot be assigned as a parent. Parents must be base products"}
                )
            
            if instance and instance.variants.exists():
                raise serializers.ValidationError(
                    {"parent_uuid": "A product that already has variants cannot become a variant of another product"}
                )

        query_set = Product.objects.filter(name=name, parent=parent, variant_name=variant_name)
    
        if instance:
            query_set = query_set.exclude(pk=instance.pk)

        if query_set.exists():
            raise serializers.ValidationError(
                {"non_field_errors": "A product with this exact name, parent, and variant already exists"}
            )
        
        if parent is not None:
            if not variant_name or variant_name.strip() == "":
                raise serializers.ValidationError(
                    {"variant_name": "If a product has a parent, it must provide a variant name"}
                )
            
        if parent is None:
            if variant_name:
                raise serializers.ValidationError(
                    {"variant_name": "base products can not have a variant_name"}
                )
        
        return validated_data
            

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # پاسخ محصول پایه، گونه‌ها و نظرها را دارد و موجودی خودش را نمایش نمی‌دهد.
        if data.get("parent_uuid") is None:
            data.pop("variant_name", None)
            data.pop("parent_uuid", None)
            data.pop("stock", None)
            data.pop("available_stock", None)
            

        # پاسخ گونه، اطلاعات خرید و والد را نگه می‌دارد و بخش‌های ویژه محصول پایه حذف می‌شوند.
        if data.get("parent_uuid") is not None:
            data.pop("variants", None)
            data.pop("recent_reviews", None)
            data.pop("review_count", None)
            data.pop("avg_rating", None)

        return data


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializes user reviews, enforcing strict content moderation 
    to prevent spam (phone/email) and profanity.
    """
    # نویسنده و محصول در view تعیین می‌شوند و از ورودی کاربر قابل تغییر نیستند.
    user = serializers.ReadOnlyField(source="user.email")
    product = serializers.ReadOnlyField(source="product.uuid")

    class Meta:
        model = Review
        fields = ["id", "product", "user", "description", "rating", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at", "user", "product"]

    def validate_description(self, value):
        """Applies content moderation rules to the review text."""
        if re.search(phone_regex, value):
            raise serializers.ValidationError("Reviews cannot contain a phone number")
        
        if re.search(email_regex, value):
            raise serializers.ValidationError("Reviews cannot contain a email address")
        
        # واژه‌های فهرست‌شده به صورت زیررشته و بدون حساسیت به حروف انگلیسی جست‌وجو می‌شوند.
        lower_value = value.lower()
        for word in banned_word:
            if word in lower_value:
                raise serializers.ValidationError(f"Reviews cannot contain the word '{word}'")
            
        return value
    

class ReplySerializer(serializers.ModelSerializer):
    """Serializes review replies with the same content moderation rules as reviews."""
    # نویسنده و نظر مقصد را view از کاربر جاری و مسیر درخواست مشخص می‌کند.
    user = serializers.ReadOnlyField(source="user.email")
    review = serializers.ReadOnlyField(source="review.id")

    class Meta:
        model = Reply
        fields = ["id", "review", "user", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at", "user", "review"]

    def validate_description(self, value):
        """Applies content moderation rules to the reply text."""
        if re.search(phone_regex, value):
            raise serializers.ValidationError("Replies cannot contain a phone number")
        
        if re.search(email_regex, value):
            raise serializers.ValidationError("Replies cannot contain a email address")
        
        lower_value = value.lower()
        for word in banned_word:
            if word in lower_value:
                raise serializers.ValidationError(f"Replies cannot contain the word '{word}'")
            
        return value
