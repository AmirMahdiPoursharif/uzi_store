# بارگذاری پکیج config، برنامه Celery را هم برای فرمان‌های worker و beat در دسترس می‌گذارد.
from .celery import app as celery_app

__all__ = ("celery_app", )