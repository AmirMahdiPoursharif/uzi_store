from django.apps import AppConfig


class OrderAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'order'
    # روابط رشته‌ای مدل‌ها و migrationها به این برچسب وابسته‌اند.
    label = 'order_app'
