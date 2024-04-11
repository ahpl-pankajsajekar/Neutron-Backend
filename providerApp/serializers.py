from rest_framework import serializers

class DCSerializer(serializers.Serializer):
    FirstName = serializers.CharField(max_length=150)
    LastName = serializers.CharField(max_length=150)

class EmpanelmentSerializer(serializers.Serializer):
    FirstName = serializers.CharField(max_length=150)
    LastName = serializers.CharField(max_length=150)
    
class SelfEmpanelmentSerializer(serializers.Serializer):
    DCName = serializers.CharField(max_length=180)
    pan_image = serializers.ImageField()

# Change DC Status
class DCStatusChangeSerializer(serializers.Serializer):
    DCStatus = serializers.CharField(max_length=250)
