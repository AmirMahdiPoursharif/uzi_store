from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser, AllowAny
from rest_framework.throttling import ScopedRateThrottle
from product.models import Category, Product, Review, Reply
from product.api.serializers import (CategorySerializer, ProductSerializer,
                                           ReviewSerializer, ReplySerializer)
from product.api.permissions import IsOwnerOrAdmin
from django.shortcuts import get_object_or_404
from django.db.models import Count, Avg
from django.core.cache import cache
from product.api.pagination import ProductPagination


# =============================================================================
# PUBLIC ENDPOINTS (USER VIEWS)
# =============================================================================


class UserProductListView(APIView):
    """
    Public API view to retrieve a paginated, cached list of visible products
    Supports filtering by category slug
    """
    permission_classes = [AllowAny]
    pagination_class = ProductPagination
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "product_category_read"

    def get(self, request):
        # 1. Extract query parameters
        category_slug = request.query_params.get("category", "all")
        page_number = request.query_params.get("page", "1")
        page_size = request.query_params.get("size", "20")

        # 2. Check cache to serve response faster
        current_cache_version = cache.get("products_cache_version", 1)
        cache_key = f"v{current_cache_version}_user_products(category:{category_slug},page:{page_number},page_size:{page_size})"
        products_cached_data = cache.get(cache_key)

        if products_cached_data is not None:
            return Response(products_cached_data, status=status.HTTP_200_OK)

        # 3. Fetch from DB if cache misses (Only 'show=True' products)
        products = Product.objects.filter(show=True, parent__isnull=True).annotate(
            review_count=Count("reviews"),
            avg_rating=Avg("reviews__rating")
        ).prefetch_related("variants")

        # Apply category filter if specified
        if category_slug != "all":
            products = products.filter(category__slug=category_slug)

        # 4. Paginate and Serialize
        paginator = self.pagination_class() 
        paginated_products = paginator.paginate_queryset(products, request)

        if paginated_products is not None:
            serializer = ProductSerializer(paginated_products, many=True)
            products_paginated_response = paginator.get_paginated_response(serializer.data)

            # Cache the paginated response for 15 minutes
            cache.set(cache_key, products_paginated_response.data, timeout=900)
            return products_paginated_response

        # Fallback if pagination is bypassed
        serializer = ProductSerializer(products, many=True)
        cache.set(cache_key, serializer.data, timeout=900)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class UserProductDetailView(APIView):
    """Public API view to retrieve detailed information for a specific visible product"""
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "product_category_read"

    def get(self, request, uuid):
        product = get_object_or_404(Product.objects.annotate(
            review_count=Count("reviews"),
            avg_rating=Avg("reviews__rating")
        ), uuid=uuid, show=True)

        serializer = ProductSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class UserCategoryListView(APIView):
    """Public API view to retrieve a cached list of all product categories"""
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "product_category_read"

    def get(self, request):
        cache_key = "categories_list"
        categories = cache.get(cache_key)

        if not categories:
            # Fetch from DB and cache for 30 minutes if cache misses
            categories = Category.objects.all()
            categories = list(categories)
            cache.set(cache_key, categories, timeout=1800)

        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class UserCategoryDetailView(APIView):
    """Public API view to retrieve specific category details"""
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "product_category_read"

    def get(self, request, category_slug):
        category = get_object_or_404(Category, slug=category_slug)
        serializer = CategorySerializer(category)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================
    

class AdminProductListView(APIView):
    """
    Admin API view to list all products (including hidden ones) 
    or create a new product
    """
    permission_classes = [IsAdminUser]
    pagination_class = ProductPagination

    def get(self, request):
        # Admin cache logic (similar to user logic but queries ALL products)
        category_slug = request.query_params.get("category", "all")
        page_number = request.query_params.get("page", "1")
        page_size = request.query_params.get("size", "20")

        current_cache_version = cache.get("products_cache_version", 1)
        cache_key = f"v{current_cache_version}_admin_products(category:{category_slug},page:{page_number},page_size:{page_size})"
        products_cached_data = cache.get(cache_key)

        if products_cached_data is not None:
            return Response(products_cached_data, status=status.HTTP_200_OK)

        # Notice: No 'show=True' filter for admins
        products = Product.objects.all().annotate(
            review_count=Count("reviews"),
            avg_rating=Avg("reviews__rating")
        )
        
        if category_slug != "all":
            products = products.filter(category__slug=category_slug)

        paginator = self.pagination_class() 
        paginated_products = paginator.paginate_queryset(products, request)

        if paginated_products is not None:
            serializer = ProductSerializer(paginated_products, many=True)
            products_paginated_response = paginator.get_paginated_response(serializer.data)
            cache.set(cache_key, products_paginated_response.data, timeout=900)
            return products_paginated_response

        serializer = ProductSerializer(products, many=True)
        cache.set(cache_key, serializer.data, timeout=900)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Create a new product"""
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class AdminProductDetailView(APIView):
    """Admin API view for retrieving, updating, or deleting a specific product"""
    permission_classes = [IsAdminUser]
    
    def get(self, request, uuid):
        product = get_object_or_404(Product.objects.annotate(
            review_count=Count("reviews"),
            avg_rating=Avg("reviews__rating")
        ), uuid=uuid)

        serializer = ProductSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request, uuid):
        product = get_object_or_404(Product, uuid=uuid)
        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, uuid):
        product = get_object_or_404(Product, uuid=uuid)
        product.show = False
        product.save()
        return Response(
            {"message": "Product successfully deactivated and hidden from users"},
            status=status.HTTP_200_OK
        )


class AdminCategoryListView(APIView):
    """Admin API view to list all categories or create a new one"""
    permission_classes = [IsAdminUser]

    def get(self, request):
        cache_key = "categories_list"
        categories = cache.get(cache_key)

        if not categories:
            categories = Category.objects.all()
            categories = list(categories)
            cache.set(cache_key, categories, timeout=1800)

        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            cache.delete("categories_list")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class AdminCategoryDetailView(APIView):
    """Admin API view to retrieve or delete a specific category"""
    permission_classes = [IsAdminUser]
        
    def get(self, request, category_slug):
        category = get_object_or_404(Category, slug=category_slug)
        serializer = CategorySerializer(category)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def delete(self, request, category_slug):
        category = get_object_or_404(Category, slug=category_slug)

        if category.products is not None:
            return Response(
                {"error": "There are some products that connected to this category, please delete them first"},
                status=status.HTTP_400_BAD_REQUEST
            )

        category.delete()
        cache.delete("categories_list")
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    
# =============================================================================
# REVIEWS & REPLIES ENDPOINTS
# =============================================================================
    

class ProductReviewListView(APIView):
    """
    API view to list reviews for a product or allow authenticated 
    users to create/update their own review
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'review_reply_create_read'

    def get(self, request, uuid):
        product = get_object_or_404(Product, uuid=uuid)
        reviews = product.reviews.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request, uuid):
        product = get_object_or_404(Product, uuid=uuid)

        if product.parent:
            product = product.parent

        # Check if the user has already reviewed this product
        has_reviewed = Review.objects.filter(product=product, user=request.user).exists()

        # If review exists, perform a partial update instead of creation
        if has_reviewed:
            return Response(
                {"error": "You have already reviewed this product"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ReviewSerializer(data=request.data)

        if serializer.is_valid():    
            serializer.save(product=product, user=request.user)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ReviewDetailView(APIView):
    """API view to retrieve, update, or delete a specific review"""

    # Enforce object-level permissions (Only owner can edit, admin can delete)
    permission_classes = [IsOwnerOrAdmin]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'review_reply_create_read'

    def get(self, request, review_id):
        review = get_object_or_404(Review, pk=review_id)
        self.check_object_permissions(request, review)
        serializer = ReviewSerializer(review)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request, review_id):
        review = get_object_or_404(Review, pk=review_id)
        self.check_object_permissions(request, review)
        serializer = ReviewSerializer(review, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, review_id):
        review = get_object_or_404(Review, pk=review_id)
        self.check_object_permissions(request, review)
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class ReviewReplyListView(APIView):
    """API view to list replies for a specific review or create a new reply"""
    permission_classes = [IsAuthenticatedOrReadOnly]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'review_reply_create_read'

    def get(self, request, review_id):
        review = get_object_or_404(Review, pk=review_id)
        replies = review.replies.all()
        serializer = ReplySerializer(replies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request, review_id):
        review = get_object_or_404(Review, pk=review_id)

        has_replied = Reply.objects.filter(review=review, user=request.user).exists()

        if has_replied:
            return Response(
                {"error": "You already have a reply on this review"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ReplySerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user, review=review)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ReplyDetailView(APIView):
    """API view to update or delete a specific reply"""
    permission_classes = [IsOwnerOrAdmin]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'review_reply_create_read'

    def patch(self, request, reply_id):
        reply = get_object_or_404(Reply, pk=reply_id)
        self.check_object_permissions(request, reply)
        serializer =ReplySerializer(reply, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, reply_id):
        reply = get_object_or_404(Reply, pk=reply_id)
        self.check_object_permissions(request, reply)
        reply.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
