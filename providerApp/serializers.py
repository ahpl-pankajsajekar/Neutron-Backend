from rest_framework import serializers

class DCSerializer(serializers.Serializer):
    FirstName = serializers.CharField(max_length=150)
    LastName = serializers.CharField(max_length=150)

class EmpanelmentSerializer(serializers.Serializer):
    FirstName = serializers.CharField(max_length=150)
    LastName = serializers.CharField(max_length=150)
    
class SelfEmpanelmentSerializer(serializers.Serializer):
    providerName = serializers.CharField(max_length=250)
    Regi_number = serializers.CharField(max_length=250)
    Owner_name = serializers.CharField(max_length=250)
    PanCard_number = serializers.CharField(max_length=250)
    pan_image = serializers.ImageField()

class SelfEmpanelmentVerificationSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=180)
    DCVerificationStatus = serializers.CharField(max_length=180)

# Change DC Status
class DCStatusChangeSerializer(serializers.Serializer):
    DCStatus = serializers.CharField(max_length=250)
