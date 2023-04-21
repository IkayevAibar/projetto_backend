from rest_framework import serializers
from .models import Residence, Apartment, Attachment, Cluster, Floor, Layout, City

class ResidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Residence
        fields = '__all__'

class ApartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Apartment
        fields = '__all__'

class AttachmentSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(max_length=None, allow_empty_file=False, use_url=True)
    class Meta:
        model = Attachment
        fields = '__all__'

class ClusterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cluster
        fields = '__all__'

class FloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = '__all__'

class LayoutSerializer(serializers.ModelSerializer):
    pdf = serializers.FileField(max_length=None, allow_empty_file=False, use_url=True)
    class Meta:
        model = Layout
        fields = '__all__'

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = '__all__'

