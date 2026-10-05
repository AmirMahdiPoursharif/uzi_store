from django.core.exceptions import ValidationError
from cart.api.serializers import CartSerializer, CartItemSerializer
from cart.models import Cart, CartItem
from product.models import Product
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated


class CartDetailView(APIView):
    """
    API view for retrieving the authenticated user's current shopping cart.
    Creates a new cart on the fly if one does not exist (e.g., for legacy users).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CartAddItemView(APIView):
    """
    API view to add a new product to the cart or increment its quantity 
    if it already exists. It strictly validates the requested quantity 
    against the actual available stock of the product.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_uuid = str(request.data.get("product_uuid"))
        
        try:
            quantity = int(request.data.get("quantity", 1))
        except ValueError:
            return Response(
                {"error": "quantity must be a integer"}, status=status.HTTP_400_BAD_REQUEST
            )
        
        if quantity <= 0:
            return Response(
                {"error": "quantity must be positive number and greater than 0"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate that the requested product exists and is available for sale
        try:
            product = Product.objects.get(uuid=product_uuid, show=True)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError:
            return Response({"error": "Please enter a valid uuid"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Prevent for adding base product in cart 
        if product.parent is None:
            return Response(
                {"error": "Base products cannot be added to the cart Please select a specific variant"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 2. Initial stock check: Ensure the warehouse has enough items for this single request
        if product.available_stock() < quantity:
            return Response(
                {"error": f"Insufficient stock. Only {product.available_stock()} items are available"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Retrieve the cart and check if this product is already in it
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item = CartItem.objects.filter(cart=cart, product=product).first()
        
        if cart_item:
            new_total_quantity = cart_item.quantity + quantity
            if product.available_stock() < new_total_quantity:
                return Response(
                    {"error": f"You already have {cart_item.quantity} items in your cart. Total available stock is {product.available_stock()}."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update the existing item's quantity
            cart_item.quantity = new_total_quantity
            cart_item.save()
        else:
            # Create a brand new item in the cart
            cart_item = CartItem.objects.create(cart=cart, product=product, quantity=quantity)

        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CartRemoveItemView(APIView):
    """API view to completely remove a specific product from the user's cart."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_uuid = request.data.get("product_uuid")
        cart = Cart.objects.get(user=request.user)

        # Ensure the underlying product actually exists
        try:
            product = Product.objects.get(uuid=product_uuid)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError:
            return Response({"Please enter a valid uuid"}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure the item is actually present in the user's cart before deletion
        try:
            cart_item = CartItem.objects.get(cart=cart, product=product)
        except CartItem.DoesNotExist:
            return Response({"error": "Item not in cart"}, status=status.HTTP_404_NOT_FOUND)

        cart_item.delete()
        return Response({"message": "Item successfully deleted from cart"}, status=status.HTTP_204_NO_CONTENT)
