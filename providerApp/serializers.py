from rest_framework import serializers


class DCSerializer(serializers.Serializer):
    FirstName = serializers.CharField(max_length=150)
    LastName = serializers.CharField(max_length=150)

class EmpanelmentSerializer(serializers.Serializer):
    FirstName = serializers.CharField(max_length=150)
    LastName = serializers.CharField(max_length=150)