from rest_framework.permissions import BasePermission

class IsAuthenticatedMongoUser(BasePermission):
    """Allows access only to authenticated users"""
    def has_permission(self, request, view):
        return bool(request.user and getattr(request.user, 'is_authenticated', False))


class IsAdminRole(BasePermission):
    """
    Allows access only to users with the 'admin' role.
    Note: Admin inherits all permissions.
    """
    def has_permission(self, request, view):
        if not (request.user and getattr(request.user, 'is_authenticated', False)):
            return False
        return getattr(request.user, 'role', '') == 'admin'


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission to allow owners to edit their note or allow admins full access.
    """
    def has_object_permission(self, request, view, obj):
        if not (request.user and getattr(request.user, 'is_authenticated', False)):
            return False
        if request.user.role == 'admin':
            return True
        user_id = str(obj.get('userId', ''))
        return user_id == str(request.user.id)
