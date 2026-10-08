from django.apps import AppConfig


class DashboardAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'
    # این برچسب نام پایدار برنامه در migrationها و روابط پایگاه داده است.
    label = 'dashboard_app'
