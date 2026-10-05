from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission to allow read-only access to anyone,
    but restrict editing/deleting exclusively to the object's owner or an admin.
    """
    def has_object_permission(self, request, view, obj):
        # Allow read permissions (GET, HEAD, OPTIONS) for any request
        if request.method in SAFE_METHODS:
            return True
        
        # Deny write operations if the user is not logged in
        if not request.user.is_authenticated:
            return False
        
        # Grant access if the user owns the object or has superuser privileges
        return obj.user == request.user or request.user.is_staff