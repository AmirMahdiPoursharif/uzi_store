import logging

from common.http import post_json
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def verify_payment(payment_id, order_id):
    # استعلام مستقل، شناسه پرداخت دریافتی را همراه شناسه سفارش به درگاه می‌فرستد.
    data = {
        "id": payment_id,
        "order_id": order_id,
    }
    verify_url = settings.PAYMENT_URLS["payment_gateway_verify_url"]
    try:
        return post_json(
            verify_url,
            data,
            timeout=5,
            headers=settings.PAYMENT_HEADERS
        )
    except Exception as e:
        # None به callback می‌گوید که پاسخی قابل استفاده از استعلام دریافت نشده است.
        logger.exception(
            f"{timezone.now()} | gateway connection error | order id: {order_id} \n error: {e}"
        )
        return None
