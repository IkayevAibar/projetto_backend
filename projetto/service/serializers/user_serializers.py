from django.utils import timezone

import re

from rest_framework import serializers

from service.models import User

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'sms_verified', 'is_active', 'date_joined']


class UserSerializer(serializers.ModelSerializer):
    empty_password = serializers.SerializerMethodField(read_only=True)

    def get_empty_password(self, obj):
        return obj.check_password('')
    
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'sms_verified', 'password', 'is_active', 'empty_password', 'date_joined']
        extra_kwargs = {'password': {'write_only': True}}
    
    def validate_username(self, value):
        if not re.match(r'^\+[0-9]+$', value):
            raise serializers.ValidationError('User\'s phone must start with "+" and contain only digits.')
        return value
    
    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.full_name = validated_data.get('full_name', instance.full_name)
        password = validated_data.get('password')
        if password:
            instance.set_password(password)
        
        instance.updated_at = timezone.now()
        instance.save()
        return instance

class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username','full_name','sms_verified' , 'password']
        extra_kwargs = {'password': {'write_only': True, 'required': False}}
    
    def validate_username(self, value):
        if not re.match(r'^\+[0-9]+$', value):
            raise serializers.ValidationError('User\'s phone must start with "+" and contain only digits.')
        return value
    

class SendSMSRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)

class VerifySMSRequestSerializer(serializers.Serializer):
    otp_code = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=True)

class ChangePasswordSerializer(serializers.Serializer):
    phone = serializers.CharField(required=True)
    otp_code = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)
