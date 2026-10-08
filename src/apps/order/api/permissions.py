from rest_framework.permissions import BasePermission


class IsManager(BasePermission):
    # دسترسی پنل سفارش به کاربر احراز هویت‌شده با پرچم is_staff محدود است.
    def has_permission(self, request, view):
        return bool(
            request.user
            and
            request.user.is_authenticated
            and
            request.user.is_staff
        )
