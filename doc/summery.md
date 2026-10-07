# خلاصهٔ آخرین تغییرات کد

این سند تغییرات انجام‌شده در شاخهٔ `dev` (بدون commit) را شرح می‌دهد.

| فایل | نوع تغییر |
|---|---|
| `src/apps/accounts/serializers.py` | اصلاح |
| `src/apps/accounts/views.py` | اصلاح |
| `src/apps/cart/apps.py` | اصلاح |
| `src/apps/order/api/views.py` | اصلاح |
| `src/config/settings.py` | افزودن |

---

## دلایل تغییرات

این تغییرات به‌صورت هدفمند برای بستن نقص‌های مستندشده در `doc/ARCHITECTURE.md` §19 و `CLAUDE.md` انجام شده‌اند:

1. **رفع خطای ۵۰۰ هنگام ثبت‌نام** — `RegisterSerializer.create()` فیلد `phone` را می‌خواند، ولی این فیلد در `Meta.fields` نبود و `create_user` به‌خاطر نبودِ شماره تلفن `ValueError` می‌داد.
2. **فعال کردن ساخت خودکار سبد خرید** — `cart/apps.py` متد `ready()` را override کرده بود ولی `cart.signals` را ایمپورت نمی‌کرد؛ در نتیجه سیگنالِ ساختِ `Cart` هرگز ثبت نمی‌شد و درخواست‌های سبد خرید با `Cart.DoesNotExist` خطا می‌دادند.
3. **درست کردن ویوی جزئیات سفارش مدیر** — `ManagerOrderPanelView` نه `queryset` داشت و نه `serializer_class`، پا به محض فراخوانی `AssertionError` می‌داد؛ افزودن scope throttle هم برای رفع `ImproperlyConfigured` لازم بود.
4. **هم‌راستا کردن ارسال مجدد OTP با جریان پیامکی** — `ResendotpView` هنوز ایمیلی فکر می‌کرد (جستجو با `email`، ارسال با `send_otp_email`) در حالی که کل جریان OTP بر اساس شماره تلفن و پیامک است؛ این باعث می‌شد ارسال مجدد کد هیچ‌وقت کار نکند.
5. **پاک‌سازی کدِ مرده** — حذف تابعِ به‌اشتباهِ خارج‌از‌کلاسِ `validate_phone` و ایمپورتِ تکراری `User`، و حذف بلوک `TODO` که مشکلش حل شده بود.

---

## ۱. `src/apps/accounts/serializers.py`

**چرا تغییر کرد:** باگ شناخته‌شدهٔ ثبت‌نام (Registration 500) که در `CLAUDE.md` و `doc/ARCHITECTURE.md` §19 ثبت شده بود: فیلد `phone` در `Meta.fields` سریالایزر نبود، ولی متد `create()` آن را می‌خواند و `create_user` به‌خاطر نبودِ شماره تلفن خطا می‌داد.

**چه چیزی تغییر کرد:**

- فیلد `phone` به‌صورت صریح به `RegisterSerializer` اضافه شد:
  `phone = serializers.CharField(required=True, allow_null=False, allow_blank=False, max_length=15)`
  - دلیل صریح‌نویسی: فیلد مدل `null=True, blank=True` است، پس فیلدِ خودکارِ `ModelSerializer` اختیاری می‌شد و اعتبارسنجِ E.164 فیلد `phonenumber_field` هم فرمت محلی `09…` را رد می‌کرد.
- `'phone` به لیست `Meta.fields` اضافه شد:
  `fields = ['email', 'phone', 'first_name', 'last_name', 'password', 'password2']`
- یک تابع سطحِ ماژولِ به‌اسم `validate_phone(self, value)` حذف شد. این تابع به‌اشتباه بیرون از کلاس و با پارامتر `self` تعریف شده بود، بنابراین هیچ‌وقت به‌عنوان validator اجرا نمی‌شد؛ اعتبارسنجی واقعی همان `validate_phone` داخلِ کلاس (خط ۶۹) انجام می‌شود.

---

## ۲. `src/apps/accounts/views.py`

**چرا تغییر کرد:** `ResendotpView` هنوز روی ایمیل کار می‌کرد، در حالی که جریان OTP بر اساس شماره تلفن است؛ کدِ قبلی هم `send_otp_email` را صدا می‌زد (توابع ارسال هم ایمیلی بودند).

**چه چیزی تغییر کرد:**

- `from .models import User` حذف شد، چون در انتهای ایمپورت‌ها از قبل `User = get_user_model()` وجود دارد (رفع ایمپورتِ تکراری/مرده).
- در `ResendotpView.post`:
  - خروجی خطا از «ایمیل معتبر وارد کنید» به «شماره تلفن معتبر وارد کنید» تغییر کرد.
  - `email = serializer.validated_data['email']...` جایگزین شد با `phone = serializer.validated_data['phone']`.
  - کلید کشِ محدودیتِ ارسال مجدد از `resend_otp_<email>` به `resend_otp_<phone>` تغییر کرد.
  - جستجوی کاربر از `User.objects.get(email=...)` به `User.objects.get(phone=...)` تغییر کرد.
  - به‌جای `otp = otp_generate(email); send_otp_email(email, otp)` فقط `otp_generate(phone)` صدا زده می‌شود، چون این تابع خودش کد را در `otp_<phone>` کش می‌کند و SMS را می‌فرستد.
  - پیام‌های پاسخ (موفقیت، عدم وجود کاربر) و لاگ از ایمیل به شماره تلفن تغییر کرد.

---

## ۳. `src/apps/cart/apps.py`

**چرا تغییر کرد:** باگ شناخته‌شدهٔ «سبد خرید خودکار ساخته نمی‌شود»: متد `ready()` فقط docstring داشت و `cart.signals` را ایمپورت نمی‌کرد، در نتیجه سیگنالِ ساختِ خودکار `Cart` ثبت نمی‌شد و `cart/api/views.py` با `Cart.objects.get()` بدون گارد خطا می‌داد.

**چه چیزی تغییر کرد:**

- داخل `ready()` خط `import cart.signals` اضافه شد تا سیگنال‌ها هنگام راه‌اندازی ثبت شوند.
- یک فاصلهٔ انتهایی (trailing space) در docstring اصلاح شد.

---

## ۴. `src/apps/order/api/views.py`

**چرا تغییر کرد:** باگ مستندشدهٔ `ManagerOrderPanelView`: این ویو نه `queryset` داشت و نه `serializer_class`، که باعث `AssertionError` در DRF می‌شد (قسمت TODO انتهای فایل همین خطا را توضیح داده بود).

**چه چیزی تغییر کرد:**

- `serializer_class = OrderDetailSerializer` به `ManagerOrderPanelView` اضافه شد.
- `queryset` با `prefetch_related` تعریف شد تا کل درختِ `order_items → product → category` در دو کوئری واکشی شود (جلوگیری از N+1). `select_related("user")` عمداً اضافه نشد چون `user` به‌صورت pk رندر می‌شود و join آن بی‌اثر است.
- ایمپورت `Prefetch` به `django.db.models` اضافه شد.
- بلوک `TODO`/توضیح خطا از انتهای فایل حذف شد چون مشکل حل شده است.
- کامنت امضای انتهای فایل حفظ شد.

---

## ۵. `src/config/settings.py`

**چرا تغییر کرد:** ویوی `ManagerOrderPanelView` با `throttle_scope = "manager"` تعریف شده، اما scope مربوطه در `DEFAULT_THROTTLE_RATES` نبود؛ DRF در این حالت `ImproperlyConfigured` برمی‌گرداند.

**چه چیزی تغییر کرد:**

- نرخِ throttle جدید اضافه شد:
  `'manager': '60/min'`

---

## جمع‌بندی

این تغییرات چهار مورد از نقص‌های فهرست‌شده در `doc/ARCHITECTURE.md` §19 را می‌بندند:

1. خطای ۵۰۰ ثبت‌نام به‌خاطر نبود `phone` در `Meta.fields`.
2. ثبت‌نشدن سیگنال ساختِ خودکار سبد خرید (`cart.apps.ready`).
3. خرابی `ManagerOrderPanelView` به‌خاطر نبود `queryset`/`serializer_class`.
4. ناسازگاری جریان OTP با شماره تلفن در `ResendotpView` (ایمیل ↔ پیامک).

در مجموع: ۵ فایل، ۳۲ خط افزوده و ۳۳ خط حذف‌شده.
