# middleware.py
from Account.serializers import get_user_by_email
import jwt
from django.conf import settings
from django.http import JsonResponse
from rest_framework import status
from django.utils.deprecation import MiddlewareMixin


class JWTAuthenticationMiddleware:
    print("-> JWTAuthenticationMiddleware") 
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        token = request.headers.get('Authorization')
        if token:
            try:
                payload = jwt.decode(token, settings.SECRET_KEY)
                user = get_user_by_email(payload.get('email'))
                request.user = user 
            except jwt.ExpiredSignatureError:
                return JsonResponse({'error': 'Token has expired'}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return JsonResponse({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            request.user = None
        response = self.get_response(request)
        return response


