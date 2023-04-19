from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Residence, Apartment, Attachment, Cluster, Floor, Layout
from .serializers import ResidenceSerializer, ApartmentSerializer, AttachmentSerializer, ClusterSerializer, FloorSerializer, LayoutSerializer

class ResidenceViewSet(viewsets.ModelViewSet):
    queryset = Residence.objects.all()
    serializer_class = ResidenceSerializer

    @action(detail=True, methods=['get'])
    def clusters(self, request, pk=None):
        residence = self.get_object()
        clusters = residence.clusters.all()
        serializer = ClusterSerializer(clusters, many=True)
        return Response(serializer.data)

class ClusterViewSet(viewsets.ModelViewSet):
    queryset = Cluster.objects.all()
    serializer_class = ClusterSerializer

    @action(detail=True, methods=['get'])
    def floors(self, request, pk=None):
        cluster = self.get_object()
        floors = cluster.floors.all()
        serializer = FloorSerializer(floors, many=True)
        return Response(serializer.data)

class FloorViewSet(viewsets.ModelViewSet):
    queryset = Floor.objects.all()
    serializer_class = FloorSerializer

    @action(detail=True, methods=['get'])
    def apartments(self, request, pk=None):
        floor = self.get_object()
        apartments = floor.apartments.all()
        serializer = ApartmentSerializer(apartments, many=True)
        return Response(serializer.data)

class ApartmentViewSet(viewsets.ModelViewSet):
    queryset = Apartment.objects.all()
    serializer_class = ApartmentSerializer

    @action(detail=True, methods=['get'])
    def layouts(self, request, pk=None):
        apartment = self.get_object()
        layouts = apartment.layouts.all()
        serializer = LayoutSerializer(layouts, many=True)
        return Response(serializer.data)

class LayoutViewSet(viewsets.ModelViewSet):
    queryset = Layout.objects.all()
    serializer_class = LayoutSerializer

class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer