from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from .models import Residence, Apartment, Attachment, Cluster, Floor, Layout, City, Ticket, TicketAttachment
from .serializers import ResidenceSerializer, ApartmentSerializer, AttachmentSerializer, ClusterSerializer, FloorSerializer, LayoutSerializer, CitySerializer, TicketSerializer, TicketAttachmentSerializer

from django_filters.rest_framework import DjangoFilterBackend

from django.db.models import Q
class ResidenceViewSet(viewsets.ModelViewSet):
    queryset = Residence.objects.all()
    serializer_class = ResidenceSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['city']
    search_fields = ['title', '^title', '=title']

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(title__iexact=search_query) |
                Q(city__name__icontains=search_query)
            )
        return queryset
    
    @action(detail=True, methods=['get'])
    def clusters(self, request, pk=None):
        residence = self.get_object()
        clusters = residence.clusters.all()
        serializer = ClusterSerializer(clusters, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def get_residence_tree(self, request, pk=None):
        residence = self.get_object()
        clusters = residence.clusters.all()

        tree = []
        for cluster in clusters:
            floors = cluster.floors.all()
            floors_list = []
            for floor in floors:
                apartments = floor.apartments.all()
                apartments_list = []
                for apartment in apartments:
                    apartments_list.append({
                        'id': apartment.id,
                        'name': apartment.name,
                        'area': apartment.area,
                        'rooms': apartment.rooms,
                    })
                floors_list.append({
                    'id': floor.id,
                    'name': floor.name,
                    'apartments': apartments_list
                })
            tree.append({
                'id': cluster.id,
                'name': cluster.name,
                'floors': floors_list,
            })

        return Response(tree)

class ClusterViewSet(viewsets.ModelViewSet):
    queryset = Cluster.objects.all()
    serializer_class = ClusterSerializer
    permission_classes = [AllowAny]

    @action(detail=True, methods=['get'])
    def floors(self, request, pk=None):
        cluster = self.get_object()
        floors = cluster.floors.all()
        serializer = FloorSerializer(floors, many=True)
        return Response(serializer.data)

class FloorViewSet(viewsets.ModelViewSet):
    queryset = Floor.objects.all()
    serializer_class = FloorSerializer
    permission_classes = [AllowAny]
    
    @action(detail=True, methods=['get'])
    def apartments(self, request, pk=None):
        floor = self.get_object()
        apartments = floor.apartments.all()
        serializer = ApartmentSerializer(apartments, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('residence_id', openapi.IN_QUERY, description="ID of the residence", type=openapi.TYPE_INTEGER),
        openapi.Parameter('cluster_id', openapi.IN_QUERY, description="ID of the cluster", type=openapi.TYPE_INTEGER),
    ])
    def list(self, request, *args, **kwargs):
        # Получаем переданные параметры из запроса
        residence_id = request.query_params.get('residence_id')
        cluster_id = request.query_params.get('cluster_id')

        # Проверяем, что оба параметра переданы
        if not (residence_id and cluster_id):
            return Response({'detail': 'residence_id and cluster_id query params are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Получаем соответствующий Residence и Cluster
        try:
            residence = Residence.objects.get(id=residence_id)
            cluster = Cluster.objects.get(id=cluster_id, residence_id=residence)
        except (Residence.DoesNotExist, Cluster.DoesNotExist):
            return Response({'detail': 'Residence or Cluster not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Фильтруем этажи по переданным параметрам
        floors = self.queryset.filter(cluster=cluster)

        # Сериализуем и возвращаем результат
        serializer = self.serializer_class(floors, many=True)
        return Response(serializer.data)

class ApartmentViewSet(viewsets.ModelViewSet):
    queryset = Apartment.objects.all()
    serializer_class = ApartmentSerializer
    permission_classes = [AllowAny]

    @action(detail=True, methods=['get'])
    def layouts(self, request, pk=None):
        apartment = self.get_object()
        layouts = apartment.layouts.all()
        serializer = LayoutSerializer(layouts, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('residence_id', openapi.IN_QUERY, description="ID of the residence", type=openapi.TYPE_INTEGER),
        openapi.Parameter('cluster_id', openapi.IN_QUERY, description="ID of the cluster", type=openapi.TYPE_INTEGER),
        openapi.Parameter('floor_id', openapi.IN_QUERY, description="ID of the floor", type=openapi.TYPE_INTEGER),
    ])
    def list(self, request, *args, **kwargs):
        # Получаем переданные параметры из запроса
        residence_id = request.query_params.get('residence_id')
        cluster_id = request.query_params.get('cluster_id')
        floor_id = request.query_params.get('floor_id')

        # Проверяем, что оба параметра переданы
        if not (residence_id and cluster_id and floor_id):
            return Response({'detail': 'residence_id and cluster_id and floor_id query params are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Получаем соответствующий Residence и Cluster
        try:
            residence = Residence.objects.get(id=residence_id)
            cluster = Cluster.objects.get(id=cluster_id, residence_id=residence)
            floor = Floor.objects.get(id=floor_id, cluster_id=cluster)
        except (Residence.DoesNotExist, Cluster.DoesNotExist, Floor.DoesNotExist):
            return Response({'detail': 'Residence or Cluster or Floor not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Фильтруем этажи по переданным параметрам
        apartments = self.queryset.filter(floor_id=floor)

        # Сериализуем и возвращаем результат
        serializer = self.serializer_class(apartments, many=True)

        return Response(serializer.data)

class LayoutViewSet(viewsets.ModelViewSet):
    queryset = Layout.objects.all()
    serializer_class = LayoutSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [AllowAny]

class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [AllowAny]


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [AllowAny]

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [AllowAny]

class TicketAttachmentViewSet(viewsets.ModelViewSet):
    queryset = TicketAttachment.objects.all()
    serializer_class = TicketAttachmentSerializer
    permission_classes = [AllowAny]

