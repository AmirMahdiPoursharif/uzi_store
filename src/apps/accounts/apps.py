from django.apps import AppConfig


class AccountsAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    # این برچسب در جدول‌ها و migrationهای قبلی استفاده شده است.
    label = 'accounts_app'
