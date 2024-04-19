from rest_framework import serializers
from .models import UserMasterCollection
from rest_framework_simplejwt.tokens import RefreshToken


class UserRegistrationSerializer(serializers.Serializer):
    pass

class UserLoginSerializer(serializers.Serializer):
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(max_length=128, write_only=True)

    class Meta:
        fields = ('email', 'password', 'access', 'refresh')

    def validate(self, data):
        email = data['email'].lower()
        password = data['password']
        User = UserMasterCollection.find_one({'email': email, 'password': password})
        print(type(User), User)
        if User is None:
            print("user is none")
            try:
                UserMasterCollection.find_one({'email': email})
                raise serializers.ValidationError("Invalid login credentials!")
            except Exception as e:
                raise serializers.ValidationError(f"User does not exists!")
        try:
            if User is not None: 
                print("user is not none if cond")
                refresh = RefreshToken()
                # refresh = RefreshToken.for_user(User)
                refresh_token = str(refresh)
                access_token = str(refresh.access_token)
                print(refresh)
                validated_data = {
                    'access': access_token,
                    'refresh': refresh_token,
                    'email': User['email'],
                }
                return validated_data
            else:
                raise serializers.ValidationError("Invalid login credentials!")
            
        except Exception as e:
            raise serializers.ValidationError(f"User does not exists! {e}".format())

    def validate(self, data):
        email = data['email'].lower()
        password = data['password']
        # Find the user by email and password
        user = UserMasterCollection.find_one({'email': email, 'password': password})
        if user is None:
            raise serializers.ValidationError("Invalid login credentials!")
        # Generate tokens
        refresh = RefreshToken()
        user_id = user['_id']
        print(type(user), user , user_id)
        # refresh = RefreshToken.for_user(user)
        refresh_token = str(refresh)
        access_token = str(refresh.access_token)
        # Construct validated data
        validated_data = {
            'access': access_token,
            'refresh': refresh_token,
            'email': user['email'],
            'user_id': user_id,
        }
        return validated_data