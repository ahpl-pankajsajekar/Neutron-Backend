import datetime
import json
from rest_framework import serializers
from Account.jwt_utils import generate_jwt_token
from .models import UserMasterCollection

from django.contrib.auth.hashers import check_password

# create a tuple 
UserRole_CHOICES =(  
    (1, "Network"),  
    (2, "Legal"),  
    (3, "IT"),  
    (4, "Operation"),  
) 
zone_choice =(  
    ('NorthZone', "NorthZone"),  
    ('SouthZone', "SouthZone"),  
    ('EastZone', "EastZone"),  
    ('WestZone', "WestZone"),  
    ('All', "All"),  
) 
class UserRegistrationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    role = serializers.ChoiceField(choices=UserRole_CHOICES, required=True)
    email = serializers.EmailField(required=True)
    phone = serializers.IntegerField()
    zone = serializers.ChoiceField(choices=zone_choice, required=True)
    password = serializers.CharField(max_length=15, write_only=True, min_length=6)
    password2 = serializers.CharField(max_length=15, write_only=True, min_length=6)

    def __str__(self) -> str:
        return self.email.lower()

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

# admin verification
class AdminVerifyOnUserRegistrationSerializer(serializers.Serializer):
    pass


def get_user_by_email(email):
    return UserMasterCollection.find_one({'email': email})

from django.conf import settings
class UserLoginSerializer(serializers.Serializer):
    token = serializers.CharField(read_only=True)
    role = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(max_length=128, write_only=True, required=True)

    class Meta:
        fields = ('email', 'password', 'role', 'token')
        
    def validate(self, data):
        email = data['email'].lower()
        password = data['password']
        user_obj = get_user_by_email(email)
        # User not register
        # if user_obj is None:
        #     raise serializers.ValidationError("User Not Register!")
        if user_obj and check_password(password, user_obj['password']):
            user = user_obj
            # user = json.loads(json_util.dumps(user_obj))
            if not user['IsActive']:
                raise serializers.ValidationError("Please Wait For Admin Verification.")
        else:
            raise serializers.ValidationError("Invalid login credentials or you are not registered")
        
        # Generate JWT token
        token = generate_jwt_token(user.get('email'), user.get('name'), user.get('role'))
        # update last login 
        if user:
            UserMasterCollection.update_one({'email': email}, {'$set': {"last_login_at": datetime.datetime.now()}})
        # Construct validated data
        validated_data = {
            'email': user['email'],
            'role': user['role'],
            # 'token': token.decode('utf-8'),
            'token': token,
        }
        return validated_data
    
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(required=True, min_length=6, max_length=50)
    password2 = serializers.CharField(write_only=True, required=True, min_length=6, max_length=50)

    def validate_old_password(self, value):
        try:
            user_obj = self.context['user']
            if not check_password(value, user_obj['password']):
                raise serializers.ValidationError("Incorrect old password.")
        except KeyError:
            raise serializers.ValidationError("User object not found in request context.")
        return value
    
    def validate(self, attrs):
        password = attrs.get('password')
        password2 = attrs.pop('password2')
        if password != password2:
            raise serializers.ValidationError('Password and Confirm Password does not match.')
        return attrs
    