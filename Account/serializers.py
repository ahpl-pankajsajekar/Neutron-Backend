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
        User = UserMasterCollection.find_one({'email': email})
        print(User)
        if User is None:
            try:
                UserMasterCollection.find_one({'email': email})
                raise serializers.ValidationError("Invalid login credentials!")
            except Exception as e:
                raise serializers.ValidationError("User does not exists! {e}")
        try:
            if User is not None: 
                refresh = RefreshToken.for_user(User)
                refresh_token = str(refresh)
                access_token = str(refresh.access_token)
                validation = {
                    'access': access_token,
                    'refresh': refresh_token,
                }
                return validation
            else:
                raise serializers.ValidationError("Invalid login credentials!")
            
        except Exception as e:
            raise serializers.ValidationError("User does not exists! {e}")
