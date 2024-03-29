from rest_framework import serializers
from .models import Residence, Apartment, Attachment, Cluster, Floor, Layout, City
from datetime import timezone
class ResidenceSerializer(serializers.ModelSerializer):
    city_name = serializers.StringRelatedField(source='city.name')
    attachments = serializers.SerializerMethodField()
    class Meta:
        model = Residence
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def perform_update(self, serializer):
        serializer.save(updated_at=timezone.now())

    def get_attachments(self, obj):
        attachments = Attachment.objects.filter(residence_id=obj.id)
        return AttachmentSerializer(attachments, many=True).data

class ApartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Apartment
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def perform_update(self, serializer):
        serializer.save(updated_at=timezone.now())

class AttachmentSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(max_length=None, allow_empty_file=False, use_url=True)
    class Meta:
        model = Attachment
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def perform_update(self, serializer):
        serializer.save(updated_at=timezone.now())

class ClusterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cluster
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def perform_update(self, serializer):
        serializer.save(updated_at=timezone.now())

class FloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def perform_update(self, serializer):
        serializer.save(updated_at=timezone.now())

class LayoutSerializer(serializers.ModelSerializer):
    # pdf = serializers.FileField(max_length=None, allow_empty_file=False, use_url=True)
    class Meta:
        model = Layout
        exclude = ('pdf', )
        read_only_fields = ('created_at', 'updated_at')
    
    def perform_update(self, serializer):
        serializer.save(updated_at=timezone.now())

class LayoutRetrieveSerializer(serializers.ModelSerializer):
    pdf = serializers.FileField(max_length=None, allow_empty_file=False, use_url=True)
    class Meta:
        model = Layout
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def perform_update(self, serializer):
        serializer.save(updated_at=timezone.now())

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def perform_update(self, serializer):
        serializer.save(updated_at=timezone.now())
