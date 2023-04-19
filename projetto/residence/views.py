from rest_framework import viewsets
from .models import Residence, Apartment, Attachment, Cluster, Floor, Layout
from .serializers import ResidenceSerializer, ApartmentSerializer, AttachmentSerializer, ClusterSerializer, FloorSerializer, LayoutSerializer

class ResidenceViewSet(viewsets.ModelViewSet):
    queryset = Residence.objects.all()
    serializer_class = ResidenceSerializer

class ApartmentViewSet(viewsets.ModelViewSet):
    queryset = Apartment.objects.all()
    serializer_class = ApartmentSerializer

class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer

class ClusterViewSet(viewsets.ModelViewSet):
    queryset = Cluster.objects.all()
    serializer_class = ClusterSerializer

class FloorViewSet(viewsets.ModelViewSet):
    queryset = Floor.objects.all()
    serializer_class = FloorSerializer

class LayoutViewSet(viewsets.ModelViewSet):
    queryset = Layout.objects.all()
    serializer_class = LayoutSerializer

