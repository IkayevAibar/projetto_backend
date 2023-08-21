from celery.result import AsyncResult

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.decorators import action


from service.tasks import start_task
from ..models import Order
from ..serializers.order_serializers import OrderSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    http_method_names = ['get', 'post', 'put', 'patch']

    @action(detail=True, methods=['get'], permission_classes = [AllowAny])
    def generate_pdf(self, request, pk=None):
        """Генерация pdf"""
        if pk is None:
            return Response({'message': "order id is required"})

        try:
            int(pk)
        except:
            return Response({'message': "order id must be a number"})

        order = self.queryset.get(pk=pk)

        result = start_task.delay(order.id)

        url = request.build_absolute_uri(f'/orders/{order.id}/check_pdf_status/?task_id={result.id}')
        
        return Response({
            'message': "pdf is generating",
            'task_id': result.id,
            'check_pdf_status': url
            })
    
    @action(detail=True, methods=['get'], permission_classes = [AllowAny])
    def check_pdf_status(self, request, pk=None):
        task_id = request.query_params.get('task_id')

        if task_id is None:
            return Response({'message': "task_id is required"})

        
        task = AsyncResult(task_id)
        if task.state == 'SUCCESS':
            url = request.build_absolute_uri(task.result)
            return Response({'message': "pdf is ready", 'url': url})
        elif task.state == 'FAILURE':
            return Response({'message': "pdf generating is failed"})
        else:
            return Response({'message': "pdf is generating"})
   