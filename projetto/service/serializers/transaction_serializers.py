from collections import OrderedDict

from rest_framework import serializers

from ..models import TransactionResponce, TransactionPayment, TransactionStatus, TransactionCancel, TransactionRevoke

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

