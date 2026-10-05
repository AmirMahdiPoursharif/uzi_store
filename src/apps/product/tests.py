from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from unittest.mock import patch, MagicMock
from rest_framework.test import APITestCase
from rest_framework import status
from product.models import Category, Product, Review, Reply
from product.custom_cache import FallbackCache

User = get_user_model()


class CacheSignalsTests(TestCase):
    """
    Integration tests to verify that Django signals correctly manage 
    cache versioning when product data is modified.
    """
    def setUp(self):
        """Clear the cache before each test to ensure a clean state."""
        cache.clear()

    def test_cache_version_increments_on_product_save(self):
        """
        Verify that creating or saving a product triggers a signal 
        that increments the global products cache version.
        """
        cache_key = "products_cache_version"
        cache.set(cache_key, 1, timeout=None)
        
        category = Category.objects.create(name="device")
        product = Product.objects.create(name="labtop", price=1000, category=category)
        
        new_cache_version = cache.get(cache_key)
        self.assertEqual(new_cache_version, 2)

    def test_cache_version_increments_on_product_delete(self):
        """
        Ensure that deleting a product triggers a signal to increment 
        the cache version, effectively invalidating stale data.
        """
        cache_key = "products_cache_version"

        category = Category.objects.create(name="device")
        product = Product.objects.create(name="phone", price=800, category=category)

        cache.set(cache_key, 5, timeout=None)
        product.delete()
        new_cache_version = cache.get(cache_key)
        self.assertEqual(new_cache_version, 6)

    def test_cache_version_increments_on_review_save(self):
        """
        Verify that creating or saving a review triggers a signal 
        that increments the global products cache version.
        """
        cache_key = "products_cache_version"

        category = Category.objects.create(name="device")
        product = Product.objects.create(name="phone", price=1000, category=category)
        user = User.objects.create_user(
            email="test@uzi.com", password="123", is_active=True, phone="09141111111")

        cache.set(cache_key, 1, timeout=None)

        Review.objects.create(product=product, user=user, description="Great", rating=5)

        new_cache_version = cache.get(cache_key)
        self.assertEqual(new_cache_version, 2)

    def test_cache_version_increments_on_review_delete(self):
        """
        Ensure that deleting a review triggers a signal to increment 
        the cache version, effectively invalidating stale data.
        """
        cache_key = "products_cache_version"

        category = Category.objects.create(name="device")
        product = Product.objects.create(name="phone", price=800, category=category)
        user = User.objects.create_user(
            email="test@uzi.com", password="123", is_active=True, phone="09141111111")
        review = Review.objects.create(product=product, user=user, description="Good", rating=4)

        cache.set(cache_key, 5, timeout=True)

        review.delete()
        new_cache_version = cache.get(cache_key)

        self.assertEqual(new_cache_version, 6)


class FallbackCacheTests(TestCase):
    """
    Unit tests for the FallbackCache utility, ensuring reliable data retrieval 
    and dual-write consistency across primary and secondary caches.
    """
    def setUp(self):
        """Initialize the custom FallbackCache instance with dummy configurations."""
        self.cache = FallbackCache("default", {
            "PRIMARY": "redis",
            "FALLBACK": "local"
        })

    @patch("product.custom_cache.caches")
    def test_get_reads_from_primary(self, mock_caches):
        """
        Test that the system retrieves data from the primary cache (Redis) 
        under normal operating conditions.
        """
        mock_primary = MagicMock()
        mock_primary.get.return_value = "cached_value"

        # Route the request to the mocked primary cache
        mock_caches.__getitem__.side_effect = lambda x: mock_primary if x == "redis" else MagicMock()

        # Perform the read operation
        result = self.cache.get("my_key")

        # Assert the value is retrieved correctly from the primary cache
        self.assertEqual(result, "cached_value")
        mock_primary.get.assert_called_once_with("my_key", None, version=None)

    @patch("product.custom_cache.caches")
    def test_get_falls_back_when_primary_fails(self, mock_caches):
        """
        Verify that if the primary cache raises an exception (e.g., connection error),
        the system gracefully falls back to read from the secondary cache (local memory).
        """
        mock_primary = MagicMock()
        mock_fallback = MagicMock()

        # Simulate primary cache failure and fallback cache success
        mock_primary.get.side_effect = Exception("Redis connection refused")
        mock_fallback.get.return_value = "fallback_value"

        mock_caches.__getitem__.side_effect = lambda x: mock_primary if x == "redis" else mock_fallback

        # Attempt to retrieve the value
        result = self.cache.get("my_key")

        # Assert the system returned the fallback value and both caches were queried
        self.assertEqual(result, "fallback_value")
        mock_primary.get.assert_called_once_with("my_key", None, version=None)
        mock_fallback.get.assert_called_once_with("my_key", None, version=None)

    @patch("product.custom_cache.caches")
    def test_set_perform_dual_write(self, mock_caches):
        """
        Verify dual-write behavior: ensure that setting a cache value writes 
        the data to both the primary and fallback caches simultaneously.
        """
        mock_primary = MagicMock()
        mock_fallback = MagicMock()

        mock_caches.__getitem__.side_effect = lambda x: mock_primary if x == "redis" else mock_fallback

        # Perform the write operation
        self.cache.set("my_key", "my_value", timeout=60)

        # Assert the set method was called on both cache backends
        mock_primary.set.assert_called_once_with("my_key", "my_value", timeout=60, version=None)
        mock_fallback.set.assert_called_once_with("my_key", "my_value", timeout=60, version=None)


class CompleteProductsViewsTests(APITestCase):
    """
    Integration tests for product-related views, including products, 
    categories, reviews, replies, and their associated permissions and caching.
    """
    def setUp(self):
        """
        Set up the test environment: clear cache and seed the database 
        with users of varying roles, categories, and products.
        """
        cache.clear()

        # Create test users
        self.super_user = User.objects.create_superuser(
            email="admin@uzi.com", password="123", is_active=True, phone="09142222222")
        self.normal_user = User.objects.create_user(
            email="user@uzi.com", password="123", is_active=True, phone="09141111111")
        self.other_user = User.objects.create_user(
            email="other@uzi.com", password="123", is_active=True, phone="09143333333")
        
        # Create test category and products
        self.category = Category.objects.create(name="laptop", slug="laptop")
        self.product_visible = Product.objects.create(
            name="macbook", price=2000, stock=10, show=True, category=self.category)
        self.product_hidden = Product.objects.create(
            name="asus", price=500, stock=0, show=False, category=self.category)
        
    def test_user_product_list_view(self):
        """
        Verify that a regular user can fetch a paginated list of visible products 
        filtered by category, and ensure the response is cached properly.
        """
        url = reverse("user_product_list")
        response = self.client.get(url, {"category": "laptop", "page": 1, "size": 20})

        # Assert response data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "macbook")

        # Verify caching mechanism
        cache_key = "v3_user_products(category:laptop,page:1,page_size:20)"
        self.assertIsNotNone(cache.get(cache_key))

    def test_user_product_detail_view(self):
        """
        Ensure users can access details of a visible product, 
        but receive a 404 Not Found error for hidden products.
        """
        # Test visible product
        url_valid = reverse("user_product_detail", kwargs={"uuid": self.product_visible.uuid})
        response_valid = self.client.get(url_valid)
        self.assertEqual(response_valid.status_code, status.HTTP_200_OK)

        # Test hidden product (should not be accessible)
        url_invalid = reverse("user_product_detail", kwargs={"uuid": self.product_hidden.uuid})
        response_invalid = self.client.get(url_invalid)
        self.assertEqual(response_invalid.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_category_views(self):
        """
        Test the public category list and detail views, 
        ensuring the category list generates a cache entry.
        """
        url_list = reverse("user_category_list")
        response_list = self.client.get(url_list)
        self.assertEqual(response_list.status_code, status.HTTP_200_OK)
        self.assertTrue(cache.has_key("categories_list"))

        url_detail = reverse("user_category_detail", kwargs={"category_slug": self.category.slug})
        response_detail = self.client.get(url_detail)
        self.assertEqual(response_detail.status_code, status.HTTP_200_OK)

    def test_admin_product_list_and_create(self):
        """
        Verify that an admin can view all products (including hidden ones) 
        and successfully create a new product.
        """
        self.client.force_authenticate(user=self.super_user)
        url = reverse("admin_product_list")
        
        # Test fetching products as admin
        response_get = self.client.get(url, {"category": "laptop", "page": 1, "size": 20})
        self.assertEqual(response_get.status_code, status.HTTP_200_OK)
        self.assertEqual(response_get.data["count"], 2)
        self.assertEqual(response_get.data["results"][1]["name"], "asus")

        # Verify admin-specific cache
        cache_key = "v3_admin_products(category:laptop,page:1,page_size:20)"
        self.assertIsNotNone(cache.get(cache_key))

        # Test product creation
        data = {"name": "new_product", "price": 100, "category_slug": self.category.slug, "parent_uuid": None}
        response_post = self.client.post(url, data, format="json")
        self.assertEqual(response_post.status_code, status.HTTP_201_CREATED)

    def test_admin_product_detail_get_patch_delete(self):
        """
        Test full CRUD operations (Retrieve, Update, Delete) 
        on a specific product by an admin user.
        """
        self.client.force_authenticate(user=self.super_user)
        url = reverse("admin_product_detail", kwargs={"uuid": self.product_visible.uuid})

        # Retrieve
        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, status.HTTP_200_OK)

        # Update
        update_data = {"name": "updated macbook", "price": 2500, "category_slug": self.category.slug}
        response_put = self.client.patch(url, update_data)
        self.assertEqual(response_put.status_code, status.HTTP_200_OK)

        # Delete
        response_delete = self.client.delete(url)
        self.assertEqual(response_delete.status_code, status.HTTP_200_OK)

    def test_admin_category_views(self):
        """
        Verify admin capabilities for category management, 
        including listing, creating, retrieving, and deleting categories.
        """
        self.client.force_authenticate(user=self.super_user)
        url_list = reverse("admin_category_list")

        # Retrieve list and verify cache
        response_list = self.client.get(url_list)
        self.assertEqual(response_list.status_code, status.HTTP_200_OK)
        self.assertTrue(cache.has_key("categories_list"))

        # Create a new category
        data = {"name": "phone", "slug": "smartwatch"}
        response_post = self.client.post(url_list, data)
        self.assertEqual(response_post.status_code, status.HTTP_201_CREATED)

        # Retrieve and delete specific category
        url_detail = reverse("admin_category_detail", kwargs={"category_slug": self.category.slug})
        response_detail = self.client.get(url_detail)
        self.assertEqual(response_detail.status_code, status.HTTP_200_OK)

        response_detail = self.client.delete(url_detail)
        self.assertEqual(response_detail.status_code, status.HTTP_204_NO_CONTENT)

    def test_product_review_list_view(self):
        """
        Test retrieving reviews and the access controls for posting/updating reviews.
        Unauthenticated users should be blocked from posting.
        """
        url = reverse("product_reviews", kwargs={"uuid": self.product_visible.uuid})

        # Public retrieval
        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, status.HTTP_200_OK)

        review_create_data = {"description": "great", "rating": 5}

        # Unauthorized creation attempt
        response_post_fail = self.client.post(url, review_create_data)
        self.assertEqual(response_post_fail.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authorized creation
        self.client.force_authenticate(user=self.normal_user)
        response_post_create = self.client.post(url, review_create_data)
        self.assertEqual(response_post_create.status_code, status.HTTP_201_CREATED)

        review_update_data = {"description": "not bad", "rating": 3}
        response_post_duplicate = self.client.post(url, review_update_data)

        self.assertEqual(response_post_duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response_post_duplicate.data)

    def test_review_detail_view_permissions(self):
        """
        Ensure strict Object-Level Permissions for reviews:
        - Anyone can view.
        - Only the owner and admins can update and delete
        """
        review = Review.objects.create(
            product=self.product_visible, user=self.normal_user, description="test", rating=4)
        url = reverse("review_detail", kwargs={"review_id": review.id})

        # Public read access
        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, status.HTTP_200_OK)

        # Unauthorized edit attempt by a different user
        self.client.force_authenticate(user=self.other_user)
        response_put_intruder = self.client.patch(url, {"description": "unauthorized edit"})
        self.assertEqual(response_put_intruder.status_code, status.HTTP_403_FORBIDDEN)

        # Authorized edit by the owner
        self.client.force_authenticate(user=self.normal_user)
        response_put_owner = self.client.patch(url, {"description": "authorized edit"})
        self.assertEqual(response_put_owner.status_code, status.HTTP_200_OK)

        # Admin delete access
        self.client.force_authenticate(user=self.super_user)
        response_delete_admin = self.client.delete(url)
        self.assertEqual(response_delete_admin.status_code, status.HTTP_204_NO_CONTENT)

    def test_reply_views(self):
        """
        Test the complete lifecycle and permissions of review replies:
        Creation, owner updates, permission denials for non-owners, and admin deletion.
        """
        review = Review.objects.create(
            product=self.product_visible, user=self.normal_user, description="test", rating=4)
        url_list = reverse("review_replies", kwargs={"review_id": review.id})

        # Retrieve replies
        response_get = self.client.get(url_list)
        self.assertEqual(response_get.status_code, status.HTTP_200_OK)

        # Unauthorized reply creation attempt
        response_post = self.client.post(url_list, {"description": "reply"})
        self.assertEqual(response_post.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authorized reply creation
        self.client.force_authenticate(user=self.other_user)
        response_post = self.client.post(url_list, {"description": "reply"})
        self.assertEqual(response_post.status_code, status.HTTP_201_CREATED)
        reply_id = response_post.data["id"]

        url_detail = reverse("reply_detail", kwargs={"reply_id": reply_id})

        # Owner updating their own reply
        response_put_owner = self.client.patch(url_detail, {"description": "authorized updated reply"})
        self.assertEqual(response_put_owner.status_code, status.HTTP_200_OK)

        # Non-owner attempting to update the reply
        self.client.force_authenticate(user=self.normal_user)
        response_put_intruder = self.client.patch(url_detail, {"description": "unauthorized updated reply"})
        self.assertEqual(response_put_intruder.status_code, status.HTTP_403_FORBIDDEN)

        # Admin deleting the reply
        self.client.force_authenticate(user=self.super_user)
        response_delete = self.client.delete(url_detail)
        self.assertEqual(response_delete.status_code, status.HTTP_204_NO_CONTENT)

    
class ProductVariantIntegrationTests(APITestCase):
    """
    Integration tests to verify the self-referencing parent-child architecture 
    for product variants, ensuring correct database relations, view filtering, 
    and review routing.
    """
    def setUp(self):
        self.super_user = User.objects.create_superuser(
            email="admin@uzi.com", password="123", is_active=True, phone="09142222222")    
        self.user = User.objects.create_user(
            email="user@uzi.com", password="123", is_active=True, phone="09141111111")
        self.category = Category.objects.create(name="phone", slug="phone")
        self.parent_product = Product.objects.create(
            category= self.category, name="iphone13", price=0, stock=0, show=True, parent=None)
        
        self.variant_black = Product.objects.create(
            category=self.category, name="iphone13", variant_name= "black - 256GB",
            price=700, stock=10, show=True, parent=self.parent_product)

        self.variant_white = Product.objects.create(
            category=self.category, name="iphone13", variant_name="white - 512GB",
            price=600, stock=2, show=True, parent=self.parent_product)
        
        self.standard_product = Product.objects.create(
            category=self.category, name="galaxy S24", price=850,
            stock=5, show=True, parent=None)
        
    def test_model_parent_child_relationship(self):
        """
        Verify that child variants correctly link to their parent product 
        and can be accessed via the 'variants' related_name.
        """
        self.assertEqual(self.parent_product.variants.count(), 2)
        self.assertEqual(self.variant_black.parent, self.parent_product)
        self.assertTrue(self.variant_black.show)

    def test_product_list_only_shows_parents_and_includes_variants(self):
        """
        Ensure public product lists only display base (parent) products, 
        embedding their associated variants within the JSON response payload.
        """
        url = reverse("user_product_list")
        response = self.client.get(url)
        results = response.data.get("results", response.data)
        
        self.assertEqual(len(results), 2)

        parent_data = next(item for item in results if item["uuid"] == str(self.parent_product.uuid))

        self.assertIn("variants", parent_data)
        self.assertEqual(len(parent_data["variants"]), 2)
        self.assertEqual(parent_data["variants"][0]["variant_name"], "black - 256GB")

    def test_admin_product_list_shows_all_products(self):
        """
        Verify admins bypass the parent-only filter and can view all products 
        (both base products and individual variants) as flat records.
        """
        self.client.force_authenticate(user=self.super_user)
        url = reverse("admin_product_list")
        response = self.client.get(url)
        
        results = response.data.get("results", response.data)
        
        self.assertEqual(len(results), 4)

    def test_review_on_variant_redirects_to_parent(self):
        """
        Ensure reviews submitted against a specific child variant (e.g., Black iPhone) 
        are automatically aggregated and linked to the base parent product.
        """
        self.client.force_authenticate(user=self.user)
        url = reverse("product_reviews", kwargs={"uuid": self.variant_black.uuid})

        review_data = {"description": "wow", "rating": 5}
        response = self.client.post(url, review_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.parent_product.reviews.count(), 1)
        self.assertEqual(self.variant_black.reviews.count(), 0)


class ProductValidationIntgreationTests(TestCase):
    """
    tests to ensure the data integrity rules inside the Product model's 
    clean() method and serializer validation logic are strictly enforced.
    """
    def setUp(self):
        self.category = Category.objects.create(name="device", slug="device")
        self.base_product = Product.objects.create(
            category=self.category, name="iphone", price=1300)
        
    def test_product_cannot_be_its_own_parent(self):
        """Ensure a product throws a ValidationError if it tries to parent itself."""
        self.base_product.parent = self.base_product
        with self.assertRaisesMessage(ValidationError, "A product cannot be its own parent"):
            self.base_product.save()

    def test_variant_cannot_be_a_product(self):
        """Verify that multi-level nesting is blocked (a variant cannot have children)."""
        variant1 = Product.objects.create(
            category=self.category, name="iphone13", parent=self.base_product,
            variant_name="Black - 256GB", price=1500)

        variant2 = Product(
            category=self.category, name="iphone15", parent=variant1, 
            variant_name="White - 512GB", price=1700
        )
        
        with self.assertRaisesMessage(ValidationError, "A variant cannot be assigned as a parent. Parents must be base products"):
            variant2.save()

    def test_variant_must_have_variant_name(self):
        """
        Ensure that if a product is created as a child (has a parent),
        the variant_name is mandatory
        """
        invalid_variant = Product(
            category=self.category, name="iphone17", parent=self.base_product, price=2000)
        
        with self.assertRaisesMessage(ValidationError, "If a product has a parent, it must provide a variant name"):
            invalid_variant.save()
