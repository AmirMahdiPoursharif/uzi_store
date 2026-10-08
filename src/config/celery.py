import os
from celery import Celery


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

app = Celery("uzistore")

# فقط تنظیمات دارای پیشوند CELERY از تنظیمات Django خوانده می‌شوند.
app.config_from_object("django.conf:settings", namespace="CELERY")

# ماژول‌های استاندارد tasks برنامه‌ها خودکار کشف می‌شوند؛ مسیرهای دیگر در CELERY_IMPORTS هستند.
app.autodiscover_tasks()
