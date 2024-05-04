from rest_framework.permissions import BasePermission

class CustomIsAuthenticatedPermission(BasePermission):
    def has_permission(self, request, view):
        if request.customMongoUser is None:
            return False
                
        if request.customMongoUser and request.customMongoUser.get('IsActive'):
            return True
        else:
            return False


# Network User
class IsNetworkUserPermission(BasePermission):
    def has_permission(self, request, view):
        if request.customMongoUser.get('IsActive') and request.customMongoUser.get('role') == '1':
            return super().has_permission(request, view)
        return False


# legal user
class IsLegalUserPermission(BasePermission):
    def has_permission(self, request, view):
        if request.customMongoUser.get('IsActive') and request.customMongoUser.get('role') == '2':
            return super().has_permission(request, view)
        return False
