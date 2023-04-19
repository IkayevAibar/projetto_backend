from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAuthenticatedOrAdminOrReadOnly(BasePermission):
    """
    Custom permission to only allow authenticated users with admin privileges to delete objects,
    but allow all users to read them.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_staff
