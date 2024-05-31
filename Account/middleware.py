from Account.jwt_utils import decode_jwt_token
from Account.serializers import get_user_by_email
import jwt
from django.conf import settings
from django.http import JsonResponse
from rest_framework import status
from django.utils.deprecation import MiddlewareMixin

class CustomJWTAuthenticationMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        super().__init__(get_response)

    def __call__(self, request):
        token = request.headers.get('Authorization')
        # email = request.headers.get('Authorization')
        if token:
            # print(token, "got")
            try:
                payload = decode_jwt_token(token)
                if isinstance(payload, JsonResponse):
                    return payload
                user = get_user_by_email(payload.get('email'))
                # user = get_user_by_email(email)
                if user:
                    request.customMongoUser = user
                    # print("User -> ", user)
                else:
                    request.customMongoUser = None
            except jwt.ExpiredSignatureError:
                return JsonResponse({'error': 'Token has expired'}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return JsonResponse({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            request.customMongoUser = None

        response = self.get_response(request)
        return response