import datetime
from django.shortcuts import render

from rest_framework.views import APIView
from Account.serializers import UserRegistrationSerializer, UserLoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.response import Response
from .models import selfEmpanelmentCollection, UserMasterCollection

# Create your views here.
# Genrate Token manually
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

# login user
class loginAPIView(APIView):
    serializer_class = UserLoginSerializer
    permission_classes = ()

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        valid = serializer.is_valid(raise_exception=True)
        if valid:
            status_code = status.HTTP_200_OK
            response = {
                'success': True,
                'statusCode': status_code,
                'message': 'User logged in successfully',
                'authenticatedUser': {
                    'data': serializer.data,
                }
            }
            return Response(response, status=status_code)

    
# create user 
class UserRegistrationAPIView(APIView):
    def post(self, request):
        try:
            # Get data from request
            serializer = UserRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                dc_data = serializer.data
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
            # Create data in MongoDB
            result = UserMasterCollection.insert_one(request.data)
            response_data = {
                    "status": "Successful",
                    "document_id": str(result.inserted_id),
                    "message": "User created Successfully",
                    "serviceName": "UserRegistration_Service",
                    "timeStamp": datetime.datetime.now().isoformat(),
                    "code": status.HTTP_201_CREATED,
                    }
            return Response(response_data)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
   