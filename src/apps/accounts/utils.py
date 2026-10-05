import logging
import random
from common.http import HttpError, post_json
from django.conf import settings
from django.core.cache import cache

loger = logging.getLogger(__name__)

def send_sms(phone, message):
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
    otp = random.randint(100000, 999999)
    cache_key = f'otp_{phone}'
    cache.set(cache_key, otp, timeout=300)
    message = f"کد تأیید شما: {otp}"
    send_sms(phone, message)

    print("\n" + "="*50)
    print(f"📱 شماره تلفن: {phone}")
    print(f"🔑 کد تأیید: {otp}")
    print("="*50 + "\n")
    
    loger.info(f"OTP for {phone}: {otp}")
    return otp
def otp_verify(phone, code):
    cache_key = f'otp_{phone}'
    cached_code = cache.get(cache_key)
    if cached_code and str(cached_code) == str(code):
        cache.delete(cache_key)
        return True
    return False