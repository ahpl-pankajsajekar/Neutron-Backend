import datetime
import json
from rest_framework import serializers
from .models import UserMasterCollection
from rest_framework_simplejwt_mongoengine.tokens import RefreshToken

from bson import ObjectId, json_util
from django.contrib.auth.hashers import check_password

class UserRegistrationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=250)
    role = serializers.IntegerField()
    email = serializers.EmailField(required=True)
    phone = serializers.IntegerField()
    password = serializers.CharField(max_length=128, write_only=True)
    password2 = serializers.CharField(max_length=128, write_only=True)

    def validate(self, attrs):
        password = attrs.get('password')
        password2 = attrs.pop('password2')
        if password != password2:
            raise serializers.ValidationError('Password and Confirm Password does not match.')
        # validate phone number
        phone_len = len(str(attrs.get('phone')))
        if phone_len != 10:
            raise serializers.ValidationError('Enter Valid Phone Number.')
        return attrs


def get_user_by_email(email):
    return UserMasterCollection.find_one({'email': email})

import jwt
from django.conf import settings
class UserLoginSerializer(serializers.Serializer):
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    token = serializers.CharField(read_only=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(max_length=128, write_only=True, required=True)

    class Meta:
        fields = ('email', 'password', 'access', 'refresh')
        
    def validate(self, data):
        email = data['email'].lower()
        password = data['password']
        user_obj = get_user_by_email(email)
        # User not register
        # if user_obj is None:
        #     raise serializers.ValidationError("User Not Register!")
        # if user_obj is None:
        #     raise serializers.ValidationError("Invalid login credentials!")
        if user_obj and check_password(password, user_obj['password']):
            user = user_obj
            # user = json.loads(json_util.dumps(user_obj))
        else:
            raise serializers.ValidationError("Invalid login credentials or you are not registered")
        
        user_id = user.get('_id')
        user['id'] = user_id
        # Generate tokens
        # refresh = RefreshToken()
        print(type(user), user)
        # Generate JWT token
        payload = {'email': email, 'name': user.get('name'), 'role':user.get('role')  }
        token = jwt.encode(payload, settings.SECRET_KEY)
        # 
        refresh = RefreshToken.for_user(user)
        refresh_token = str(refresh)
        access_token = str(refresh.access_token)
        # update last login 
        if user:
            UserMasterCollection.update_one({'email': email}, {'$set': {"last_login_at": datetime.datetime.now()}})
        # Construct validated data
        validated_data = {
            'access': access_token,
            'refresh': refresh_token,
            'email': user['email'],
            'user_id': user_id,
            'token': token,
        }
        return validated_data
    
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    # def validate_old_password(self, value):
    #     user = self.context['request'].user
    #     if not user.check_password(value):
    #         raise serializers.ValidationError("Incorrect old password.")
    #     return value
    
    def validate(self, attrs):
        password = attrs.get('password')
        password2 = attrs.pop('password2')
        if password != password2:
            raise serializers.ValidationError('Password and Confirm Password does not match.')
        return attrs
    