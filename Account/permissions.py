from rest_framework.permissions import BasePermission

class CustomPermission(BasePermission):
    def has_permission(self, request, view):
        # Add your custom logic here
        # For example, allow access only for authenticated users
        print("permission class ", request.user)
        # return request.user and request.user.is_authenticated
        if request.user:
            return request.user
        else:
            return False
