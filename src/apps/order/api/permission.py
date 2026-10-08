from rest_framework.permissions import BasePermission, IsAuthenticated

class IsManager(BasePermission):
    # این تعریف نیز مجوز مدیریت را از احراز هویت و پرچم is_staff تشخیص می‌دهد.
    def has_permission(self, request, view):
        return (
            request.user
            and
            request.user.is_authenticated
            and
            request.user.is_staff
        )
