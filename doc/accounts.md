# اپ accounts؛ ثبت‌نام و ورود

[بازگشت به راهنما](README.md)

این اپ هویت کاربر، ثبت‌نام با OTP پیامکی و ورود با JWT را مدیریت می‌کند. پروفایل، تغییر رمز و حذف حساب در اپ [dashboard](dashboard.md) پیاده شده‌اند، ولی مسیرهای آن‌ها هم زیر `/api/auth/` ثبت شده است.

## مدل و جریان داخلی

مدل `User` جایگزین کاربر پیش‌فرض Django است. `email` یکتا و شناسهٔ ورود است؛ `phone` نیز یکتاست. نام و نام خانوادگی، `is_active`، `is_staff`، مجوزهای Django و زمان ساخت حساب ذخیره می‌شوند. مدیر مدل برای `create_user` و `create_superuser` هم ایمیل و هم تلفن می‌خواهد؛ رمز با `set_password` هش می‌شود.

کاربر جدید با `is_active=False` ساخته می‌شود. `otp_generate` با `secrets` یک عدد شش‌رقمی تولید و برای ۳۰۰ ثانیه در کلید `otp_<phone>` کش ذخیره می‌کند. بعد پیامک را می‌فرستد؛ تأیید صحیح، کد را از کش حذف و حساب را فعال می‌کند. ثبت‌نام و تأیید، کاربر را وارد نمی‌کنند؛ ورود درخواست جداگانه دارد.

اگر حساب موجود فعال باشد، ثبت‌نام دوباره `200` و پیام تأیید قبلی می‌دهد. برای حساب موجود غیرفعال، کد جدید تولید می‌شود؛ رمز و اطلاعات حساب در این شاخه ویرایش نمی‌شوند.

## مسیرها

| متد | مسیر | ورودی / خروجی اصلی |
| --- | --- | --- |
| POST | `/api/auth/register/` | ایمیل، تلفن و رمز؛ ساخت حساب `201` یا پاسخ حساب موجود `200` |
| POST | `/api/auth/verify/` | `phone` و `code`؛ فعال‌سازی `200` |
| POST | `/api/auth/resend-otp/` | `phone`؛ ارسال مجدد `200` |
| POST | `/api/auth/login/` | `email` و `password`؛ اطلاعات کاربر و کوکی‌ها `200` |
| POST | `/api/auth/token/refresh/` | `refresh` در بدنه؛ `access` در JSON |
| POST | `/api/auth/logout/` | نیازمند ورود؛ حذف کوکی‌ها `200` |

ثبت‌نام، تأیید، ارسال مجدد، ورود و refresh به ورود قبلی نیاز ندارند. بااین‌حال روی ویوهای عمومی که authentication فعال است، فرستادن توکن نامعتبر می‌تواند پیش از اجرای ویو خطا بدهد.

در URLconf دو مسیر اضافهٔ `/api/auth/api/auth/resend-otp/` و `/api/auth/api/auth/logout/` و ثبت تکراری refresh وجود دارد. برای کلاینت از مسیرهای کوتاه جدول استفاده کنید. خروج متصل به URL در `dashboard.views.LogoutView` است.

## نمونهٔ ثبت‌نام و تأیید

`POST /api/auth/register/`:

```json
{
  "email": "buyer@example.com",
  "phone": "09123456789",
  "first_name": "سارا",
  "last_name": "احمدی",
  "password": "River!Oak47Blue",
  "password2": "River!Oak47Blue"
}
```

پاسخ ساخت حساب:

```json
{"message": "کد تایید به شماره تلفن شما ارسال شد."}
```

ایمیل، تلفن و هر دو فیلد رمز لازم‌اند؛ نام‌ها اختیاری هستند. رمز باید اعتبارسنجی Django را بگذراند، حداقل ۸ کاراکتر و حرف بزرگ، حرف کوچک، عدد و کاراکتر خاص داشته باشد و با بخش قبل از `@` ایمیل مشابه نباشد. دو رمز باید یکسان باشند. دامنهٔ `tempmail.com` پذیرفته نمی‌شود.

تلفن را در همهٔ مراحل به شکل `09xxxxxxxxx` و با ارقام انگلیسی بفرستید. serializer ثبت‌نام برخی شکل‌های `+98` را هم تبدیل می‌کند، اما تولید OTP از شمارهٔ خام درخواست استفاده می‌کند و verify فقط شکل ۱۱ رقمی `09` را می‌پذیرد؛ استفاده از یک قالب ثابت برای جلوگیری از ناسازگاری کلید کش لازم است. فیلد تلفن مدل، شمارهٔ معتبر محلی را هنگام ذخیره و جست‌وجوی ORM به قالب `+98` تبدیل می‌کند.

اگر کلید یا URL پیامک خالی باشد، کد آزمایشی را از `docker compose logs -f web` بخوانید. عدد زیر صرفاً مثال است؛ کد واقعی را جایگزین کنید:

`POST /api/auth/verify/`:

```json
{"phone": "09123456789", "code": "123456"}
```

کد غلط یا منقضی پاسخ `400` دارد. پس از تأیید می‌توانید وارد شوید. برای کد جدید، به `/api/auth/resend-otp/` بدنهٔ `{"phone":"09123456789"}` بفرستید. پاسخ `200` این مسیر برای شمارهٔ ناشناخته هم ممکن است؛ به‌تنهایی اثبات وجود حساب یا تحویل پیامک نیست.

## ورود و نگهداری نشست

`POST /api/auth/login/`:

```json
{"email": "buyer@example.com", "password": "River!Oak47Blue"}
```

```json
{
  "message": "ورود با موفقیت انجام شد",
  "user": {
    "email": "buyer@example.com",
    "first_name": "سارا",
    "last_name": "احمدی"
  }
}
```

توکن در بدنهٔ ورود نیست. پاسخ دو کوکی `access_token` و `refresh_token` با `HttpOnly=True`، `SameSite=Lax`، `Secure=False` و مسیر `/` می‌سازد. عمر کوکی access پانزده دقیقه و refresh یک روز است؛ چون `SIMPLE_JWT` سفارشی نشده، اعتبار خود توکن access طبق پیش‌فرض کتابخانه **پنج دقیقه** و refresh یک روز است. باقی ماندن کوکی به معنی معتبر بودن JWT نیست.

نمونهٔ مرورگر روی همان origin بک‌اند:

```javascript
const response = await fetch("/api/auth/login/", {
  method: "POST",
  credentials: "include",
  headers: { "Content-Type": "application/json", Accept: "application/json" },
  body: JSON.stringify({
    email: "buyer@example.com",
    password: "River!Oak47Blue"
  })
});
const data = await response.json();
if (!response.ok) throw new Error(JSON.stringify(data));

const profile = await fetch("/api/auth/profile/", {
  credentials: "include",
  headers: { Accept: "application/json" }
});
```

API هدر `Authorization: Bearer <access_token>` را نیز می‌پذیرد. در `CookieJWTAuthentication`، وجود هدر Authorization باعث می‌شود ابتدا روش هدر بررسی شود؛ توکن خراب در هدر با کوکی سالم جبران نمی‌شود. در Postman یا کلاینت دارای cookie jar می‌توانید از همان کوکی‌های ورود استفاده کنید.

### محدودیت فعلی refresh و خروج

مسیر refresh همان `TokenRefreshView` استاندارد است:

```json
{"refresh": "<refresh_token>"}
```

در حالت معتبر `{"access":"<new_access_token>"}` برمی‌گرداند. این ویو refresh را از کوکی نمی‌خواند و کوکی access جدید هم تنظیم نمی‌کند. بنابراین مرورگری که فقط کوکی HttpOnly دارد، در وضعیت فعلی راه کامل تمدید خودکار نشست ندارد. تا زمان تکمیل این قرارداد، پس از انقضای access ورود مجدد لازم است؛ در کلاینتی که خود مقدار refresh را در اختیار دارد، توکن جدید را از بدنه بگیرید و در هدر بفرستید.

خروج نیز access معتبر می‌خواهد و فقط کوکی‌ها را پاک می‌کند؛ blacklist توکن فعال نیست و توکن قبلی تا انقضا معتبر می‌ماند. تغییر رمز هم در کد فعلی ابطال همهٔ JWTهای موجود را انجام نمی‌دهد.

## محدودیت درخواست و خطاهای قابل انتظار

| عملیات | محدودیت فعلی |
| --- | --- |
| ثبت‌نام | throttle ناشناس ۳ درخواست در ساعت برای IP؛ شمارندهٔ داخلی نیز سقف ۵ درخواست موفق با TTL یک ساعت دارد |
| تأیید | throttle ناشناس ۱۰ درخواست در ساعت برای IP |
| ارسال مجدد | فاصلهٔ ۱۲۰ ثانیه برای هر تلفن و سقف ۱۰ ارسال برای IP با TTL یک ساعت |
| ورود | throttle ناشناس ۵ درخواست در دقیقه؛ ۵ شکست برای ایمیل باعث `423` و ۱۰ شکست برای IP باعث `429` با TTL پانزده دقیقه می‌شود |

شمارندهٔ تلاش ناموفق OTP و پرچم قفل از یک کلید `verify_block_<phone>` استفاده می‌کنند؛ تبدیل عدد به `True` باعث می‌شود قفل پنج‌تلاش مطابق انتظار پایدار نماند. این بخش را قفل قابل اتکا فرض نکنید.

پیام ورود حساب غیرفعال هنوز از «تأیید ایمیل» حرف می‌زند، ولی مرحلهٔ واقعی تأیید تلفن است. توابع اعتبارسنجی نام در serializer با نام متد اشتباه تعریف شده‌اند و اعتبارسنجی سفارشی نام فعلاً اجرا نمی‌شود. شکست ارسال SMS نیز مانع پاسخ موفق ثبت‌نام نمی‌شود.

صفحه‌های `/api/auth/register-page/`، `/api/auth/verify-page/` و `/api/auth/login-page/` قالب آزمایشی‌اند. صفحهٔ verify هنوز ایمیل می‌فرستد و با قرارداد فعلی تلفن هماهنگ نیست؛ نمونهٔ اتصال فرانت‌اند را از API این سند بگیرید.

## فایل‌های مرتبط

- [models.py](../src/apps/accounts/models.py): مدل و مدیر کاربر.
- [serializers.py](../src/apps/accounts/serializers.py): ورودی ثبت‌نام و OTP.
- [views.py](../src/apps/accounts/views.py) و [urls.py](../src/apps/accounts/urls.py): جریان‌ها و مسیرها.
- [authentication.py](../src/apps/accounts/authentication.py): JWT از هدر و کوکی.
- [utils.py](../src/apps/accounts/utils.py): تولید OTP و ارسال پیامک با [common](common.md).
- [admin.py](../src/apps/accounts/admin.py): مدیریت کاربر و رمز هش‌شده در پنل Django.
