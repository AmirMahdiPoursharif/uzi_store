# بستهٔ common؛ ارتباط HTTP با سرویس‌های بیرونی

[بازگشت به راهنما](README.md)

`common` یک بستهٔ Python کمکی است؛ در `INSTALLED_APPS` ثبت نشده و مدل، مایگریشن یا URL مستقل ندارد. فرانت‌اند مستقیماً آن را فراخوانی نمی‌کند. استفاده‌کنندگان فعلی، اپ [accounts](accounts.md) برای پیامک و اپ [order](order.md) برای پرداخت هستند.

## قرارداد post_json

تابع در [http.py](../src/apps/common/http.py) تعریف شده است:

```python
post_json(url, data, headers=None, timeout=10, parse_response=True)
```

| پارامتر | رفتار |
| --- | --- |
| `url` | نشانی سرویس مقصد |
| `data` | دادهٔ قابل تبدیل به JSON؛ در بدنهٔ POST فرستاده می‌شود |
| `headers` | هدرهای اضافی؛ پیش‌فرض `Content-Type: application/json` است |
| `timeout` | timeout فراخوانی urllib؛ پیش‌فرض ۱۰ ثانیه |
| `parse_response` | اگر true باشد پاسخ غیرخالی باید JSON معتبر باشد |

تابع با `urllib.request` کار می‌کند و وابستگی `requests` ندارد. پاسخ JSON را به شیء Python تبدیل می‌کند؛ الزام ندارد که پاسخ حتماً دیکشنری باشد. پاسخ خالی یا `parse_response=False` مقدار `None` می‌دهد.

برای خطای HTTP، خطای اتصال/timeout و JSON نامعتبر، `HttpError` ایجاد می‌شود. این استثنا علاوه بر پیام، `status` و `body` دارد؛ در خطای HTTP کد و متن پاسخ نگه داشته می‌شوند و در خطای شبکه ممکن است هر دو خالی باشند. اعتبارسنجی تجاری پاسخ، مانند بررسی `link` یا وضعیت موفق پرداخت، وظیفهٔ اپ فراخواننده است.

## مصرف‌کنندگان فعلی

| محل | درخواست و رفتار |
| --- | --- |
| `accounts.utils.send_sms` | بدنهٔ `receptor` و `message`، هدر `X-API-Key`، timeout ده ثانیه و `parse_response=False` |
| `order.api.views.Payment` | ایجاد پرداخت با مبلغ سروری، timeout پنج ثانیه؛ پاسخ باید `link` داشته باشد |
| `order.api.payment_verify.verify_payment` | استعلام با `id` و `order_id`، timeout پنج ثانیه؛ خطا را می‌گیرد و `None` برمی‌گرداند |

ارسال پیامک بدون `SMS_API_KEY` یا `SMS_API_URL` اصلاً درخواست HTTP نمی‌زند؛ متن پیامک در خروجی برنامه چاپ و `False` برگردانده می‌شود. در حالت ارسال واقعی، بدنهٔ پاسخ بررسی تجاری نمی‌شود. `otp_generate` نیز نتیجهٔ ارسال را شرط موفقیت ثبت‌نام قرار نمی‌دهد.

در شروع پرداخت، `HttpError` به پاسخ `502` API تبدیل می‌شود. شکست استعلام پرداخت در callback فعلی پاسخ `500` دارد. این تفاوت بخشی از قرارداد موجود است.

## افزودن یک مصرف‌کنندهٔ جدید

الگوی نمونه برای توسعه‌دهنده؛ URL نمونه را در محیط واقعی فراخوانی نکنید:

```python
from common.http import HttpError, post_json

def create_remote_resource(service_url, api_key, payload):
    try:
        result = post_json(
            service_url,
            payload,
            headers={"X-API-Key": api_key},
            timeout=5,
        )
    except HttpError:
        return None
    if not isinstance(result, dict):
        return None
    return result
```

قبل از استفادهٔ تجاری، فیلدهای لازم پاسخ را بررسی و خطا را متناسب با API خود تبدیل کنید. retry خودکار، idempotency، صف ارسال پیامک یا قطع موقت فراخوانی سرویس خراب در این ابزار پیاده نشده است؛ تکرار درخواست پرداخت ممکن است اثر جانبی سرویس مقصد را تکرار کند.

تنظیم کلیدها و نشانی‌ها در [راهنمای راه‌اندازی](README.md) و [settings.py](../src/config/settings.py) توضیح داده شده است؛ کلید واقعی را در کد و نمونه‌های مستندات قرار ندهید.
