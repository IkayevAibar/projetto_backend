import re

from rest_framework import serializers

from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username','first_name', 'password']
        extra_kwargs = {'password': {'write_only': True}}
    
    def validate_username(self, value):
        if not re.match(r'^\+[0-9][0-9]+\w+', value):
            raise serializers.ValidationError('Username must start with "+" and contain only digits and letters.')
        return value
