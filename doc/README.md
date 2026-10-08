# راهنمای فارسی بک‌اند Uzi Store

این مجموعه رفتار کد موجود در تاریخ ۲۰۲۶-۱۰-۰۸ را توضیح می‌دهد؛ قابلیت‌های ناقص در سند همان اپ مشخص شده‌اند. مسیرها از [روتر اصلی](../src/config/urls.py) و ورودی و خروجی‌ها از ویوها و سریالایزرهای فعلی استخراج شده‌اند. فایل‌های قدیمی پوشهٔ `doc` ممکن است با این نسخه تفاوت داشته باشند.

## از کجا شروع کنم؟

| سند | کاربرد |
| --- | --- |
| [حساب کاربری](accounts.md) | ثبت‌نام با شماره تلفن، OTP، ورود و JWT |
| [پروفایل و تنظیمات حساب](dashboard.md) | اطلاعات شخصی، آدرس، تغییر رمز و حذف حساب |
| [محصولات](product.md) | دسته‌بندی، محصول پایه، واریانت، نظر و پاسخ |
| [سبد خرید](cart.md) | انتخاب واریانت، افزایش تعداد و حذف کالا |
| [سفارش و پرداخت](order.md) | ثبت سفارش، رزرو موجودی، درگاه و پنل مدیر |
| [ابزار مشترک HTTP](common.md) | ارتباط داخلی بک‌اند با پیامک و درگاه |

پنج اپ اول در Django نصب هستند. `common` یک بستهٔ کمکی است و API یا مدل مستقل ندارد.

## راه‌اندازی محیط توسعه

پیش‌نیاز: Docker و Docker Compose نسخهٔ ۲. فرمان‌ها را در ریشهٔ مخزن اجرا کنید.

۱. اگر `.env` ندارید، در PowerShell اجرا کنید:

```powershell
Copy-Item .env.example .env
```

در Linux/macOS معادل آن `cp .env.example .env` است. فایل موجود را بازنویسی نکنید. مقدار `SECRET_KEY` را تنظیم کنید و متغیرهای زیر را مطابق محیط خود قرار دهید:

| متغیر | کاربرد فعلی |
| --- | --- |
| `SECRET_KEY` | کلید Django و امضای پیش‌فرض JWT |
| `DEBUG`، `ALLOWED_HOSTS` | حالت اجرا و میزبان‌های مجاز؛ override توسعه، `DEBUG=True` را اعمال می‌کند |
| `WEB_PORT` | پورت وب روی میزبان؛ پیش‌فرض ۸۰۰۰ |
| `POSTGRES_DB/USER/PASSWORD` | نام و مشخصات اتصال PostgreSQL |
| `POSTGRES_HOST/PORT` | اتصال خارج Docker؛ داخل Compose همیشه `db:5432` است |
| `REDIS_LOCATION` | کش Django؛ در Compose دیتابیس صفر Redis |
| `CELERY_BROKER_URL` | صف Celery؛ در Compose دیتابیس یک Redis |
| `CELERY_RESULT_BACKEND` | نتیجهٔ تسک‌ها؛ در Compose دیتابیس دو Redis |
| `SMS_API_KEY`، `SMS_API_URL` | ارسال واقعی OTP؛ اگر یکی خالی باشد، متن پیامک در ترمینال چاپ می‌شود |
| `SMS_SENDER` | در نمونهٔ تنظیمات هست ولی کد فعلی از آن استفاده نمی‌کند |
| `PAYMENT_GATEWAY_API_KEY` | کلید درگاه؛ آدرس‌های درگاه و callback فعلاً در settings ثابت‌اند |

۲. سرویس‌ها را بالا بیاورید:

```sh
docker compose up --build -d
docker compose logs -f web
```

Compose به‌ترتیب PostgreSQL و Redis، سرویس `migrate` برای مایگریشن و جمع‌آوری فایل‌های static، سپس `web`، `worker` و `beat` را اجرا می‌کند. فایل `docker-compose.override.yaml` خودکار خوانده می‌شود؛ کد `src` به کانتینر متصل است و وب با تغییر کد بارگذاری مجدد می‌شود. بعد از تغییر تسک‌ها، `docker compose restart worker beat` لازم است.

۳. مدیر بسازید:

```sh
docker compose exec web python manage.py createsuperuser
```

ایمیل، شماره تلفن و رمز را وارد کنید. پنل Django در `http://localhost:8000/admin/` و فهرست عمومی محصولات در `http://localhost:8000/user/products/` است. برای API مدیریتی، همین مدیر باید از مسیر ورود API هم وارد شود؛ نشست پنل Django به‌تنهایی جای JWT را نمی‌گیرد.

۴. با راهنمای [محصول](product.md) دسته، محصول پایه و حداقل یک واریانت دارای موجودی بسازید. دادهٔ اولیه خودکار وارد نمی‌شود. برای انتقال داده‌های قدیمی SQLite، دستورهای [README اصلی](../README.md) را ببینید.

`docker compose down` سرویس‌ها را متوقف می‌کند و دادهٔ volumeها را نگه می‌دارد. گزینهٔ `-v` volumeهای نام‌دار، از جمله دادهٔ PostgreSQL را حذف می‌کند. فایل‌های آپلود در `src/media` و قالب‌ها در `src/templates` هستند. Redis در Compose فعلی پورت میزبان ندارد؛ برای اجرای Python خارج Docker باید دسترسی جداگانه به Redis فراهم کنید.

## قرارداد استفاده از API

- نشانی پایهٔ نمونه‌ها `http://localhost:8000` است؛ مسیرهای جدول‌ها نسبت به همین نشانی هستند.
- بدنهٔ درخواست‌ها JSON است: `Content-Type: application/json`. برای دریافت JSON، `Accept: application/json` بفرستید.
- حروف مسیرها مهم‌اند؛ مثلاً `addItem` با `additem` فرق دارد. اسلش پایانی را مطابق جدول بفرستید؛ مسیر جزئیات سفارش مدیر استثناست.
- شناسهٔ عمومی کالا `uuid`، شناسهٔ سفارش رشتهٔ `order_id` و شناسهٔ نظر و پاسخ عددی است.
- مدیر API یعنی کاربر فعال با `is_staff=True`؛ الزام `is_superuser` در permission این APIها وجود ندارد.
- پیام‌های خطا یک قالب مشترک ندارند: ممکن است `message`، `error`، `detail` یا نام فیلد باشند. فقط `message` را بررسی نکنید.
- معمولاً `400` خطای ورودی/وضعیت، `401` نیاز به ورود یا توکن نامعتبر، `403` نداشتن مجوز، `404` نبود رکورد، `405` متد ناموجود و `429` محدودیت درخواست است. روی پاسخ `204`، `response.json()` اجرا نکنید.

## اتصال فرانت‌اند و ترتیب خرید

۱. `POST /api/auth/register/` با ایمیل، تلفن و رمز؛ سپس `POST /api/auth/verify/` با تلفن و کد.
۲. `POST /api/auth/login/`؛ کوکی‌های ورود را برای درخواست‌های بعدی حفظ کنید.
۳. `GET /user/products/`؛ یک `uuid` از آرایهٔ `variants` انتخاب کنید.
۴. `POST /cart/addItem/`؛ سپس `GET /cart/` برای نمایش سبد.
۵. `POST /order/create/` با بدنهٔ `{}`؛ `data.order_id` و `data.expires_at` را نگه دارید.
۶. `POST /order/payment/<order_id>/`؛ مرورگر را به مقدار `payment_page` هدایت کنید.
۷. پس از بازگشت از درگاه، وضعیت را از `GET /order/<order_id>/` بخوانید. جزئیات callback و محدودیت‌های پرداخت در [سند سفارش](order.md) آمده است.

در مرورگر، درخواست‌های احراز هویت‌شده را با `credentials: "include"` بفرستید. کوکی‌ها `HttpOnly` هستند و JavaScript نباید برای خواندن توکن از آن‌ها استفاده کند. در Postman کوکی‌های همان میزبان را حفظ کنید؛ `localhost` و `127.0.0.1` دو میزبان متفاوت‌اند.

برای شروع، فرانت‌اند و API را پشت یک origin مشترک قرار دهید. `corsheaders` نصب است ولی فهرست originهای مجاز و مجوز ارسال credentials تنظیم نشده است؛ صرف استفاده از `credentials` اتصال cross-origin را راه نمی‌اندازد. تمدید خودکار توکن مرورگر نیز فعلاً کامل نیست؛ [محدودیت refresh](accounts.md) را پیش از پیاده‌سازی نشست بخوانید.

## اجرای پایه و بررسی توسعه

برای اجرای Gunicorn بدون override توسعه:

```sh
docker compose -f docker-compose.yaml up --build -d
```

قبل از اتصال واقعی، `DEBUG=False`، دامنه‌های مجاز، HTTPS، سرو کردن `/media/` و آدرس callback را تنظیم کنید. کوکی‌های JWT فعلی `secure=False` دارند و callback روی آدرس محلی ثابت است؛ این موارد با تغییر صرف `.env` همگی اصلاح نمی‌شوند.

فرمان‌های توسعه:

```sh
docker compose exec web python manage.py check
docker compose exec web python -m pytest
docker compose exec web python -m pytest apps/product
ruff check .
ruff format --check .
```

برخی تست‌های حساب، پروفایل و سبد هنوز با قرارداد قدیمی نوشته شده‌اند؛ وجودشان تضمین عبور کامل مجموعه نیست. `order/tests.py` تست اجرایی ندارد. این مستندات بر پایهٔ بررسی کد هستند و به معنی تأیید عملی اتصال درگاه و پیامک نیستند.

Ruff برای اجرای دستی باقی مانده است؛ پروژه دیگر هوک `pre-commit` برای الزام Ruff ندارد.

## نقشهٔ کد برای توسعه‌دهنده

تنظیمات و مسیرهای اصلی در [src/config](../src/config) هستند. `settings.py` پوشهٔ `src/apps` را به مسیر import اضافه می‌کند؛ در کد از `from product.models import Product` استفاده می‌شود.

| پوشه و نام import | برچسب Django برای مایگریشن و رابطهٔ مدل |
| --- | --- |
| `accounts` | `accounts_app` |
| `dashboard` | `dashboard_app` |
| `product` | `products_app` |
| `cart` | `cart_app` |
| `order` | `order_app` |

نام import و برچسب مدل یکسان نیستند؛ مثلاً `AUTH_USER_MODEL = "accounts_app.User"` و رابطهٔ رشته‌ای محصول `"products_app.Product"` است. هنگام تغییر اپ، سند همان اپ و مسیرهای API آن را نیز به‌روز کنید.
