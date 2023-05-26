import re

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Order, Transaction

class TokenObtainPairSerializerWithoutPassword(TokenObtainPairSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].required = False

    def validate(self, attrs):
        attrs.update({'password': ''})
        try:
            user = User.objects.get(username=attrs['username'])
            if not user.sms_verified:
                raise serializers.ValidationError('Номер телефона не подтвержден')
        except User.DoesNotExist:
            raise serializers.ValidationError('Номер телефона не найден')

        refresh = RefreshToken.for_user(user)
        tokens = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        return tokens

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username','first_name','sms_verified' , 'password','is_active' ,'date_joined']
        extra_kwargs = {'password': {'write_only': True}}
    
    def validate_username(self, value):
        if not re.match(r'^\+[0-9]+$', value):
            raise serializers.ValidationError('User\'s phone must start with "+" and contain only digits.')
        return value
    
    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        password = validated_data.get('password')
        if password:
            instance.set_password(password)
        instance.save()
        return instance

class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username','first_name','sms_verified' , 'password']
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

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"

    

class TransactionCreateSerializer(serializers.Serializer):
    pg_card_name = serializers.CharField(required=False, read_only=True)
    order_id = serializers.CharField(required=True)
    pg_description = serializers.CharField(required=False, default="Order Transaction")
    pg_card_name = serializers.CharField(required=True)
    pg_card_pan = serializers.CharField(required=True)
    pg_card_cvc = serializers.CharField(required=True)
    pg_card_month = serializers.CharField(required=True)
    pg_card_year = serializers.CharField(required=True)
    pg_auto_clearing = serializers.CharField(required=False, default="1")
    pg_testing_mode = serializers.CharField(required=False, default="1")
    pg_result_url = serializers.CharField(required=False, default="projetto.dev.factory.kz")
    pg_3ds_challenge = serializers.CharField(required=False, default="1")
    pg_param1 = serializers.CharField(required=False)
    pg_param2 = serializers.CharField(required=False)
    pg_param3 = serializers.CharField(required=False)

    class Meta:
        model = Transaction
        fields = "__all__"
