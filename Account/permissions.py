from rest_framework.permissions import BasePermission

class CustomIsAuthenticatedPermission(BasePermission):
    def has_permission(self, request, view):
        if request.customMongoUser is None:
            return False
                
        if request.customMongoUser and request.customMongoUser.get('IsActive'):
            return True
        else:
            return False


# Network User not test
class IsNetworkUserPermission(BasePermission):
    def has_permission(self, request, view):
        if request.customMongoUser is None:
            return False
        if request.customMongoUser.get('IsActive') and request.customMongoUser.get('role'):
            return True
