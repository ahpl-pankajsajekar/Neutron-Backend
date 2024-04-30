from rest_framework.permissions import BasePermission

class CustomIsAuthenticatedPermission(BasePermission):
    def has_permission(self, request, view):
        if request.customMongoUser is None:
            return False
                
        if request.customMongoUser and request.customMongoUser.get('IsActive'):
            return True
        else:
            return False

