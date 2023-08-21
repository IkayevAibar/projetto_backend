from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action

from ..models import FreedomCheckRequest, FreedomResultRequest
from ..serializers.freedom_serializers import FreedomCheckRequestSerializer, FreedomResultRequestSerializer

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.utils.decorators import method_decorator

import xml.etree.ElementTree as ET


class FreedomCheckRequestViewSet(viewsets.ModelViewSet):
    queryset = FreedomCheckRequest.objects.all()
    serializer_class = FreedomCheckRequestSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def check_url(self, request):
        """Проверка платежа"""
        serializer = FreedomCheckRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            print(serializer.data)
            print(request.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

        #TODO: some logic to check 
        #    <pg_status>rejected</pg_status>
        #    <pg_description>Платеж не разрешен</pg_description>

        # Create XML response
        xml_response = ET.Element('response')
        pg_status = ET.SubElement(xml_response, 'pg_status')
        pg_status.text = 'ok'
        pg_description = ET.SubElement(xml_response, 'pg_description')
        pg_description.text = 'Платеж разрешен'
        pg_salt = ET.SubElement(xml_response, 'pg_salt')
        pg_salt.text = serializer.data['pg_salt']
        pg_sig = ET.SubElement(xml_response, 'pg_sig')
        pg_sig.text = serializer.data['pg_sig']

        xml_string = ET.tostring(xml_response, encoding='utf-8', method='xml')

        # Return XML response
        return HttpResponse(xml_string, content_type='application/xml')

class FreedomResultRequestViewSet(viewsets.ModelViewSet):
    queryset = FreedomResultRequest.objects.all()
    serializer_class = FreedomResultRequestSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def result_url(self, request):
        """Проверка платежа"""
        serializer = FreedomResultRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        #TODO: some logic to check 
        #    <pg_status>rejected</pg_status>
        #    <pg_description>Платеж не разрешен</pg_description>

        xml_response = ET.Element('response')
        pg_status = ET.SubElement(xml_response, 'pg_status')
        pg_status.text = 'ok'
        pg_description = ET.SubElement(xml_response, 'pg_description')
        pg_description.text = 'Платеж разрешен'
        pg_salt = ET.SubElement(xml_response, 'pg_salt')
        pg_salt.text = serializer.data['pg_salt']
        pg_sig = ET.SubElement(xml_response, 'pg_sig')
        pg_sig.text = serializer.data['pg_sig']

        xml_string = ET.tostring(xml_response, encoding='utf-8', method='xml')

        # Return XML response
        return HttpResponse(xml_string, content_type='application/xml')