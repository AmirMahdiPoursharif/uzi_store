import logging

from common.http import HttpError, post_json
from django.conf import settings
from django.db import transaction
from django.db.models import F, When, IntegerField, Case
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from cart.models import Cart, CartItem
from order.models import OrderStatus, InventoryReservationStatus, Order, OrderItem, InventoryReservation
from product.models import Product
from .payment_verify import verify_payment
from .permissions import IsManager
from .serializers import OrderSerializer, OrderDetailSerializer, ManagerPanelSerializer

logger = logging.getLogger(__name__)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('HHTTP_X_Real_IP')
    return ip


class BaseView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]


# user views


class OrderList(BaseView, ListAPIView):
    serializer_class = OrderSerializer
    throttle_scope = "order"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class OrderDetail(BaseView, RetrieveAPIView):
    serializer_class = OrderDetailSerializer
    lookup_field = "order_id"
    throttle_scope = "order"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class OrderCreate(BaseView, APIView):
    serializer_class = OrderDetailSerializer
    throttle_scope = "order_create"

    @transaction.atomic
    def post(self, request):
        existing_order = Order.objects.filter(
            user=request.user,
            status=1,
            expires_at__gt=timezone.now(),
        ).exists()
        if existing_order:
            return Response({"message": "Order already exists"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response({"message": "User has no cart"}, status=status.HTTP_404_NOT_FOUND)

        cart_items = user_cart.get_cart_items()

        if cart_items is None:
            return Response({"message": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        product_ids = [item.product_id for item in cart_items]  # [1, 4, 7, 8]
        locked = {
            product.id: product for product in Product.objects.select_for_update().filter(
                id__in=product_ids,
            ).order_by("id")
        }

        # {
        #   1: <object 1>,
        #   4: <object 4>,
        #   7: <object 7>,
        #   8: <object 8>
        # }

        for item in cart_items:
            product = locked[item.product_id]
            if item.quantity > product.available_stock():
                return Response({"message": "not enough stock"}, status=status.HTTP_400_BAD_REQUEST)

        user_order = Order.objects.create(
            user=request.user
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=user_order,
                product=item.product,
                price=item.product.price,
                quantity=item.quantity,
            )
            InventoryReservation.objects.create(
                order=user_order,
                product=item.product,
                quantity=item.quantity,
            )
        user_order.set_expires_at()
        user_order.update_total_price()
        CartItem.objects.filter(cart=user_cart).delete()

        response = {
            "message": "Order created successfully",
            "data": self.serializer_class(user_order, context={"request": request}).data,
        }

        return Response(response, status=status.HTTP_201_CREATED)


class Payment(BaseView, APIView):
    throttle_scope = "payment"

    @transaction.atomic
    def post(self, request, **kwargs):
        order_id = kwargs.get("order_id")

        try:
            order = Order.objects.select_for_update().get(
                user=request.user,
                order_id=order_id
            )
        except Order.DoesNotExist:
            return Response({"message": "order does not exist"}, status=status.HTTP_404_NOT_FOUND)

        if order.status != OrderStatus.PENDING_PAYMENT or order.transaction_id:
            return Response({"message": "Order can not be paid"}, status=status.HTTP_400_BAD_REQUEST)

        if order.is_expired():
            order.expire()
            return Response({"message": "your order is expired"}, status=status.HTTP_400_BAD_REQUEST)

        amount = order.total_price
        data = {
            "order_id": f"{order_id}",
            "amount": amount,
            "name": f"{request.user.first_name} {request.user.last_name}",
            "mail": f"{request.user.email}",
            "desc": "test description",
            "callback": settings.PAYMENT_URLS["payment_gateway_callback_url"]
        }
        payment_url = settings.PAYMENT_URLS["payment_gateway_url"]

        try:
            response = post_json(
                payment_url,
                data,
                headers=settings.PAYMENT_HEADERS,
                timeout=5,
            )
        except HttpError as e:
            logger.exception(
                f"{timezone.now()} | error while sending request to payment gateway | order id {order_id} \n    because of this exception: \n   {e}",
            )
            return Response({"message": "gateway connection error"}, status=status.HTTP_502_BAD_GATEWAY)

        link = (response or {}).get("link")
        if not link:
            logger.error(
                f"{timezone.now()} | there is no link in gateway response | order id: {order_id} \n    response: \n    {response}",
            )
            return Response({"message": "gateway error"}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({"payment_page": f"{link}"}, status=status.HTTP_200_OK)


class Callback(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "callback"

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        ip = get_client_ip(request)
        params = {
            "status": request.GET.get("status"),
            "track_id": request.GET.get("track_id"),
            "id": request.GET.get("id"),
            "order_id": request.GET.get("order_id"),
        }

        try:
            status_code = int(params["status"])
        except:
            return Response({"message": "status code is incorrect"}, status=status.HTTP_400_BAD_REQUEST)

        if status_code == 10:
            order_id = params["order_id"]
            payment_id = params["id"]
            # get the correct order
            try:
                order = Order.objects.select_for_update().get(
                    order_id=order_id
                )
            except Order.DoesNotExist:
                logger.error(
                    f"{timezone.now()} | order for received callback does not exists | user ip: {ip} | order id: {order_id}"
                )
                return Response({"message": "order does not exist"}, status=status.HTTP_404_NOT_FOUND)

            if order.status == OrderStatus.PAID or order.transaction_id:
                return Response({"error": "the order is already paid"}, status=status.HTTP_400_BAD_REQUEST)

            response = verify_payment(payment_id, order_id)

            if response is None:
                return Response({"message": "gateway connection error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            try:
                if response["status"] == "100":
                    order.status = OrderStatus.PAID
                    order.transaction_id = params["id"]
                    order_items = list(order.get_order_items())
                    order.expires_at = None
                    if not order_items:
                        logger.error(f"there are no order items for order {order_id}")
                        return Response({"message":"no items found for"}, status=status.HTTP_404_NOT_FOUND)

                    order.save(
                        update_fields=[
                            "status",
                            "transaction_id",
                            "expires_at",
                        ]
                    )

                    order_product_ids = [item.product_id for item in order_items]

                    cases = [
                        When(id=order_item.product_id, then=F("stock") - order_item.quantity)
                        for order_item in order_items
                    ]

                    Product.objects.select_for_update().filter(id__in=order_product_ids).update(
                        stock=Case(*cases, output_field=IntegerField())
                    )

                    order.reservations.update(
                        status=InventoryReservationStatus.RELEASED
                    )
                else:
                    logger.warning(
                        f"{timezone.now()} | payment verification failed (user fault) | user ip: {ip}\n    {response}"
                    )
                    return Response({"message": "payment verification failed"}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.exception(
                    f"{timezone.now()} | payment verify failed | order id: {order_id}\n    error:\n   {e}\n {response['status']}"
                )
                return Response({"message": "internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response(response, status=status.HTTP_200_OK)

        else:
            return Response({"message": "payment is not completed"}, status=status.HTTP_400_BAD_REQUEST)


# admin panel views


# admin dashboard

class ManagerPanelView(ListAPIView):
    permission_classes = [IsManager]
    queryset = Order.objects.all()
    serializer_class = ManagerPanelSerializer


class ManagerOrderPanelView(RetrieveAPIView):
    permission_classes = [IsManager]
    lookup_field = "order_id"
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "manager"

# Created with ❤️ by (dizi) amirmahdi for uzi


# TODO
#   error in ManagerOrderPanelView:
#       AssertionError: 'ManagerOrderPanelView' should either include a `queryset` attribute, or override the `get_queryset()` method.
