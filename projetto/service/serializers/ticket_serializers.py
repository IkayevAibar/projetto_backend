from django.utils import timezone

from rest_framework import serializers

from service.models import Ticket, TicketAttachment


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def perform_update(self, serializer):
        serializer.save(updated_at=timezone.now())

class TicketAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketAttachment
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def perform_update(self, serializer):
        serializer.save(updated_at=timezone.now())

