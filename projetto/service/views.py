from django.shortcuts import render

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


from .permissions import IsAuthenticatedOrAdminOrReadOnly
from .models import User
from .serializers import UserSerializer, SendSMSRequestSerializer, VerifySMSRequestSerializer
from app.settings import account_sid, auth_token, verify_sid


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'send_sms', 'verify_sms']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticatedOrAdminOrReadOnly]
    
        return [permission() for permission in permission_classes]
    
    # @swagger_auto_schema(
    #     operation_description='Retrieve user by ID'
    # )
    # def retrieve(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     serializer = self.get_serializer(instance)
    #     return Response(serializer.data)
    
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.set_password(serializer.validated_data['password'])
        user.save()
        
        headers = self.get_success_headers(serializer.data)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @swagger_auto_schema(
        request_body=VerifySMSRequestSerializer,
        operation_description='Verify SMS verification code sended to your phone number'
    )
    @action(detail=False, methods=['post'], permission_classes = [AllowAny])
    def verify_sms(self, request, pk=None):
        # user = self.get_object()
        # Получение SMS code
        # ...
        
        verified_number = request.data.get('phone_number')
        otp_code = request.data.get('otp_code')
        client = Client(account_sid, auth_token)

        try:
            verification_check = client.verify.v2.services(verify_sid) \
                .verification_checks \
                .create(to=verified_number, code=otp_code)
        except TwilioRestException as e:
            return Response({'status':e.code})
        
        return Response({'status': verification_check.status})
    
    @swagger_auto_schema(
        request_body=SendSMSRequestSerializer,
        operation_description='Send SMS verification code to your phone number'
    )
    @action(detail=False, methods=['post'], permission_classes = [AllowAny])
    def send_sms(self, request, pk=None):
        # user = self.get_object()
        # Отправка SMS
        # ...
        verified_number = request.data.get('phone_number')
        client = Client(account_sid, auth_token)
        try:
            verification = client.verify.v2.services(verify_sid) \
                .verifications \
                .create(to=verified_number, channel="sms", locale="ru")
        except TwilioRestException as e:
            return Response({'status':e.code})
        
        return Response({'status': verification.status})


# class VerifySMSCode(APIView):
#     permission_classes = [AllowAny]
    
#     @swagger_auto_schema(
#         request_body=openapi.Schema(
#             type='object',
#             properties={
#                 'phone_number': openapi.Schema(
#                     type='string',
#                     description='The phone number of the user',
#                     example='+123456789'
#                 )
#             },
#             required=['phone_number']
#         )
#     )
#     def post(self, request):
        
#         verified_number = request.data.get('phone_number')
#         otp_code = request.data.get('otp_code')
        
#         client = Client(account_sid, auth_token)

#         verification_check = client.verify.v2.services(verify_sid) \
#           .verification_checks \
#           .create(to=verified_number, code=otp_code)
        
#         if verification_check.status == 'approved':
#             return Response({'message': 'OTP code verified successfully'})
#         else:
#             return Response({'message': 'OTP code verification failed'})
