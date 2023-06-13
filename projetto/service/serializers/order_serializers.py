from rest_framework import serializers
from service.models import Order

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = ('created_at', 'updated_at', 'doc')
