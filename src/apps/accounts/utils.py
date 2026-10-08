import logging
import secrets
from common.http import HttpError, post_json
from django.conf import settings
from django.core.cache import cache

loger = logging.getLogger(__name__)

def send_sms(phone, message):
    # بدون تنظیمات سرویس پیامک، پیام برای آزمایش محلی در خروجی چاپ می‌شود.
    api_key = getattr(settings, 'SMS_API_KEY', None)
    api_url = getattr(settings, 'SMS_API_URL', None)
    if not api_key or not api_url:
        print(f"\n⚠️ [تست] پیامک به {phone}: {message}\n")
        return False
    try:
        headers = {
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        }
        payload = {
            'receptor': phone,
            'message': message
        }
        # بدنه پاسخ سرویس مصرف نمی‌شود و لازم نیست JSON باشد.
        post_json(api_url, payload, headers=headers, timeout=10, parse_response=False)
        print(f"✅ پیامک به {phone} ارسال شد")
        loger.info(f"SMS sent to {phone}")
        return True

    except HttpError as e:
        print(f"❌ خطا در ارسال پیامک: {e.body or e}")
        loger.error(f"SMS error: {e} | body: {e.body}")
        return False

    except Exception as e:
        print(f"❌ خطا در ارسال پیامک: {str(e)}")
        loger.error(f"SMS exception: {str(e)}")
        return False
def otp_generate(phone):
    # کد شش‌رقمی با مهلت پنج دقیقه و با کلیدی وابسته به رشته ورودی تلفن ذخیره می‌شود.
    otp = 100000 + secrets.randbelow(900000)
    cache_key = f'otp_{phone}'
    cache.set(cache_key, otp, timeout=300)
    message = f"کد تأیید شما: {otp}"
    send_sms(phone, message)

    # Never print or log the code itself. In local development send_sms already
    # echoes the whole message to stdout when SMS_API_KEY/SMS_API_URL are unset.
    loger.info(f"OTP generated for {phone}")
    return otp
def otp_verify(phone, code):
    cache_key = f'otp_{phone}'
    cached_code = cache.get(cache_key)
    if cached_code and str(cached_code) == str(code):
        # حذف کد پس از تطبیق، مانع استفاده دوباره از همان کد می‌شود.
        cache.delete(cache_key)
        return True
    return False