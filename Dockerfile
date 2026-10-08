FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app
# کپی جداگانه وابستگی‌ها اجازه می‌دهد تغییر کد از لایه نصب قبلی استفاده کند.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd --system app && useradd --system --gid app app \
    && mkdir -p /app/src/media /app/staticfiles \
    && chown -R app:app /app

COPY --chown=app:app pytest.ini /app/pytest.ini
COPY --chown=app:app src /app/src

WORKDIR /app/src
# اجرای وب با کاربر غیرریشه انجام می‌شود و مسیرهای نوشتنی پیش‌تر به او واگذار شده‌اند.
USER app
EXPOSE 8000

# دو worker درخواست‌ها را از ورودی WSGI می‌گیرند و لاگ‌ها به خروجی کانتینر می‌روند.
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-"]
