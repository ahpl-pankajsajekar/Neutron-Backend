from django.http import JsonResponse
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status


secret_key = settings.SECRET_KEY

def generate_jwt_token(email, name, role):
    # Set token expiration time (e.g., 1 hour)
    expiration_time = datetime.utcnow() + timedelta(days=5)
    
    # Set token issue time
    issue_time = datetime.utcnow()
    
    # Create payload with expiration time and issue time
    payload = {
        'email': email,
        'name': name,
        'role': role,
        'exp': expiration_time,
        'iat': issue_time
    }

    # Generate JWT token
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    return token


def decode_jwt_token(token):
    try:
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return JsonResponse({'error': 'Token has expired'}, status=status.HTTP_401_UNAUTHORIZED)
    except jwt.InvalidTokenError:
        return JsonResponse({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)


# Generate JWT token
# token = generate_jwt_token('user@example.com', 'John Doe', 'admin')
# print("Generated Token:", token)

# # Verify JWT token
# verified_payload = decode_jwt_token(token)
# print("Verified Payload:", verified_payload)
