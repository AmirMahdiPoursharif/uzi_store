import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from order.models import Order, OrderStatus

logger = logging.getLogger(__name__)


@shared_task
def delete_expired_orders(days=30):
    # این کار فقط سفارش‌های از قبل EXPIRED را پاک می‌کند و سفارش معلق را منقضی نمی‌کند.
    time_delta = timezone.now() - timedelta(days=days)

    orders_to_delete = Order.objects.filter(
        status=OrderStatus.EXPIRED,
        expires_at__lt=time_delta,
    )

    orders_count = orders_to_delete.count()

    if orders_count == 0:
        logger.info("no expired orders for delete")
        return "No expired orders deleted"

    orders_to_delete.delete()

    logger.info(f"{orders_count} expired orders deleted")
    return f"{orders_count} expired orders deleted"
