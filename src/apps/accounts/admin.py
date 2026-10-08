from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from accounts.models import User


# Register your models here.


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Configuration for managing Users in the Django admin interface.

    Inherits from the auth UserAdmin so that passwords are hashed through
    set_password() instead of being edited as raw text. Every fieldset is
    redeclared because the stock ones reference `username` and `date_joined`,
    which this model does not have (USERNAME_FIELD is `email`).
    """
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "phone")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "acc_created_at")}),
    )
    # فرم ایجاد کاربر باید فیلدهای مدل سفارشی و دو ورودی رمز عبور را داشته باشد.
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "phone", "usable_password", "password1", "password2"),
            },
        ),
    )
    list_display = ("email", "phone", "first_name", "last_name", "is_active", "is_staff",)
    list_filter = ("is_staff", "is_superuser", "is_active", "groups",)
    search_fields = ("email", "phone", "first_name", "last_name",)
    ordering = ("email",)
    readonly_fields = ("last_login", "acc_created_at",)
