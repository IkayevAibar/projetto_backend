from rest_framework import serializers
from service.models import FreedomCheckRequest, FreedomResultRequest

class FreedomCheckRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FreedomCheckRequest
        fields = "__all__"

class FreedomResultRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FreedomResultRequest
        fields = "__all__"