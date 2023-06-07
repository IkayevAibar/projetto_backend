import re

from collections import OrderedDict

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Order, TransactionResponce, TransactionPayment, TransactionStatus, TransactionCancel, TransactionRevoke

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
    empty_password = serializers.SerializerMethodField(read_only=True)

    def get_empty_password(self, obj):
        return obj.check_password('')
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'sms_verified', 'password', 'is_active', 'empty_password', 'date_joined']
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

class ChangePasswordSerializer(serializers.Serializer):
    otp_code = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"

# class TransactionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Transaction
#         fields = "__all__"

class TransactionResponceSerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        result = super(TransactionResponceSerializer, self).to_representation(instance)
        return OrderedDict([(key, result[key]) for key in result if result[key] is not None])
    
    class Meta:
        model = TransactionResponce
        fields = "__all__"


class TransactionPaymentSerializer(serializers.ModelSerializer):
    pg_salt = serializers.CharField(required=False, read_only=True)
    pg_sig = serializers.CharField(required=False, read_only=True)
    pg_merchant_id = serializers.CharField(required=False, read_only=True)
    pg_amount = serializers.CharField(required=False, read_only=True)
    pg_currency = serializers.CharField(required=False, read_only=True)

    class Meta:
        model = TransactionPayment
        fields = "__all__"

class TransactionStatusSerializer(serializers.ModelSerializer):
    pg_salt = serializers.CharField(required=False, read_only=True)
    pg_sig = serializers.CharField(required=False, read_only=True)
    pg_merchant_id = serializers.CharField(required=False, read_only=True)
    pg_order_id = serializers.CharField(required=False, read_only=True)
    class Meta:
        model = TransactionStatus
        fields = "__all__"

class TransactionCancelSerializer(serializers.ModelSerializer):
    pg_salt = serializers.CharField(required=False, read_only=True)
    pg_sig = serializers.CharField(required=False, read_only=True)
    pg_merchant_id = serializers.CharField(required=False, read_only=True)
    class Meta:
        model = TransactionCancel
        fields = "__all__"

class TransactionRevokeSerializer(serializers.ModelSerializer):
    pg_salt = serializers.CharField(required=False, read_only=True)
    pg_sig = serializers.CharField(required=False, read_only=True)
    pg_merchant_id = serializers.CharField(required=False, read_only=True)
    pg_refund_amount = serializers.CharField(required=False, read_only=True)
    class Meta:
        model = TransactionRevoke
        fields = "__all__"
