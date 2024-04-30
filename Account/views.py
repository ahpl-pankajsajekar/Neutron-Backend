import datetime
from django.shortcuts import render

from rest_framework.views import APIView
from Account.permissions import CustomIsAuthenticatedPermission
from Account.serializers import ChangePasswordSerializer, UserRegistrationSerializer, UserLoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken # type: ignore
from rest_framework import status
from rest_framework.response import Response
from .models import UserMasterCollection

from django.contrib.auth.hashers import make_password
from pymongo.errors import DuplicateKeyError


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

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        valid = serializer.is_valid(raise_exception=True)
        if valid:
            status_code = status.HTTP_200_OK
            response = {
                'status': "Successful",
                'data': serializer.data,
                'message': 'User logged in successfully',
                "serviceName": "UserLogin_Service",
                "timeStamp": datetime.datetime.now().isoformat(),
                "code": status.HTTP_200_OK,
            }
            return Response(response, status=status_code)


# create user 
class UserRegistrationAPIView(APIView):
    def post(self, request):
        user_data = request.data
        try:
            # Get data from request
            serializer = UserRegistrationSerializer(data=user_data)
            if serializer.is_valid():
                dc_data = serializer.data
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # delete password2 from body
            del user_data['password2']
            user_data['password'] = make_password(user_data['password'])
            user_data["created_at"] = datetime.datetime.now()
            user_data["updated_at"] = datetime.datetime.now()
            user_data["IsActive"] = True

            # Create data in MongoDB
            result = UserMasterCollection.insert_one(user_data)
            response_data = {
                    "status": "Successful",
                    "document_id": str(result.inserted_id),
                    "message": "User created Successfully",
                    "serviceName": "UserRegistration_Service",
                    "timeStamp": datetime.datetime.now().isoformat(),
                    "code": status.HTTP_201_CREATED,
                    }
            return Response(response_data)
        
        except DuplicateKeyError:
            error_detail = "Duplicate key error: This email is already registered."
            return Response({'error': error_detail}, status=400)   
        

class ChangePasswordAPIView(APIView):
    permission_classes = [CustomIsAuthenticatedPermission]

    def post(self, request):
        user = request.customMongoUser
        try:
            serializer = ChangePasswordSerializer(data=request.data, context={'user': user})
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            # new dataFrame
            newData = {}
            newData['password'] = make_password(str(request.data.get('password')))
            newData["updated_at"] = datetime.datetime.now()
            # update above data in users
            UserMasterCollection.update_one({'email': user['email']}, {'$set': newData})
            response_data = {
                    "status": "Successful",
                    "message": "Change Password Successfully",
                    "serviceName": "ChangePassword_Service",
                    "timeStamp": datetime.datetime.now().isoformat(),
                    "code": status.HTTP_200_OK,
                    }
            return Response(response_data)
        
        except Exception as e:
            return Response({'error': {e}}, status=500)   