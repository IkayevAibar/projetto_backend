
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from service.models import User, Order
from service.serializers.user_serializers import  ChangePasswordSerializer, UserSerializer, UserCreateSerializer, \
                                                SendSMSRequestSerializer, VerifySMSRequestSerializer, UserListSerializer
from service.serializers.order_serializers import OrderSerializer

from app.settings import account_sid, auth_token, verify_sid



class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in 'send_sms':
            return SendSMSRequestSerializer
        elif self.action in 'verify_sms':
            return VerifySMSRequestSerializer
        elif self.action in 'restore_password':
            return ChangePasswordSerializer
        elif self.action in 'list':
            return UserListSerializer
        
        return UserSerializer
    def get_permissions(self):
        if self.action in ['create', 'send_sms_to_phone', 'verify_sms', 'restore_password']:
            permission_classes = [AllowAny]
        elif self.action in ['list', 'retrieve', 'update', 'partial_update', 'destroy', 'get_all_orders']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
    
        return [permission() for permission in permission_classes]
    
    @swagger_auto_schema(
        method='get',
        operation_summary='Get user by phone',
        operation_description='Retrieve a user by phone number.',
        manual_parameters=[
            openapi.Parameter(
                name='phone',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description='Phone number of the user.',
                required=True
            )
        ],
        responses={
            200: UserSerializer,
            404: 'User not found.'
        }
    )
    @action(detail=False, methods=['GET'])
    def get_by_phone(self, request):
        phone = request.query_params.get('phone')
        if phone:
            phone = phone.replace(' ', '')
            if not phone.startswith('+'):
                phone = '+' + phone

        try:
            user = User.objects.get(username=phone)
        except User.DoesNotExist:
            return Response({'detail': 'Пользователя с таким номер нет'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(user)

        return Response(serializer.data)

    def create(self, request):
        user_manager = User.objects
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data.get('username')
        password = serializer.validated_data.get('password')
        full_name = serializer.validated_data.get('full_name')
        sms_verified = serializer.validated_data.get('sms_verified')
        
        if sms_verified == True:
            user = user_manager.create_user(username=username, password=password, sms_verified=sms_verified, full_name=full_name)
        else:
            if(password):
                user = user_manager.create_user(username=username, password=password, sms_verified=sms_verified, full_name=full_name)
                user.save()
            else:
                raise ValidationError("Password is required for user creation.") 

        headers = self.get_success_headers(serializer.data)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    
    @swagger_auto_schema(
        request_body=VerifySMSRequestSerializer,
        operation_description='Verify SMS verification code sended to your phone number'
    )
    @action(detail=False, methods=['post'], permission_classes = [AllowAny])
    def verify_sms(self, request, pk=None):
        verified_number = request.data.get('phone_number')
        otp_code = request.data.get('otp_code')
        client = Client(account_sid, auth_token)

        try:
            verification_check = client.verify.v2.services(verify_sid) \
                .verification_checks \
                .create(to=verified_number, code=otp_code)
        except TwilioRestException as e:
            return Response({'status':e.code})
        
        if verification_check.status == 'approved':
            # Аутентификация пользователя по номеру телефона
            user = None
            try:
                user = User.objects.get(username=verified_number)
            except User.DoesNotExist:
                pass
            
            if(user):
                return Response({'status': verification_check.status, 'user_id': user.id})
            # Создание нового пользователя, если он не существует
            user = User.objects.create_user(username=verified_number, sms_verified=True)
            # Генерация токена
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            return Response({'status': verification_check.status, 'user': {'user_id': user.id, 'access_token': access_token, 'refresh_token': refresh_token}})
        else:
            return Response({'status': verification_check.status})

    @swagger_auto_schema(
        request_body=SendSMSRequestSerializer,
        operation_description='Send SMS verification code to your phone number'
    )
    @action(detail=False, methods=['post'], permission_classes = [AllowAny])
    def send_sms_to_phone(self, request, pk=None):
        verified_number = request.data.get('phone_number')
        client = Client(account_sid, auth_token)
        try:
            verification = client.verify.v2.services(verify_sid) \
                .verifications \
                .create(to=verified_number, channel="sms", locale="ru")
        except TwilioRestException as e:
            return Response({'status':e.code})
        
        return Response({'status': verification.status})

    @action(detail=True, methods=['get'], permission_classes = [AllowAny])
    def send_sms(self, request, pk=None):
        if pk:
            try:
                user = User.objects.get(id=pk)
            except User.DoesNotExist:
                return Response({'status': 'Пользователь не найден'})
        else:
            return Response({'status': 'ID должен быть указан'})
        
        # Отправка SMS
        verified_number = user.username
        client = Client(account_sid, auth_token)
        try:
            verification = client.verify.v2.services(verify_sid) \
                .verifications \
                .create(to=verified_number, channel="sms", locale="ru")
        except TwilioRestException as e:
            return Response({'status':e.code})
        
        return Response({'status': verification.status})
 
    @action(detail=True, methods=['get'])
    def get_all_orders(self, request, pk=None):
        status = request.query_params.get('status')

        orders = Order.objects.filter(user=pk) #, status='paid')

        if status is not None:
            orders = orders.filter(status=status)

        serializer = OrderSerializer(orders, many=True)
        return Response({'orders': serializer.data})
    
    @swagger_auto_schema(
        request_body=ChangePasswordSerializer,
        operation_description='Восстановление пароля'
    )
    @action(detail=False, methods=['post'])
    def restore_password(self, request):
        phone = request.data.get('phone')
        try:
            user = User.objects.get(username=phone)
        except User.DoesNotExist:
            return Response({'status': 'Пользователь c таким номерем не найден'})
        
        verified_number = user.username
        otp_code = request.data.get('otp_code')
        client = Client(account_sid, auth_token)

        try:
            verification_check = client.verify.v2.services(verify_sid) \
                .verification_checks \
                .create(to=verified_number, code=otp_code)
        except TwilioRestException as e:
            return Response({'status':e.code})

        if verification_check.status == 'approved':
            password = request.data.get('password')
            confirm_password = request.data.get('confirm_password')
            if(password != confirm_password):
                return Response({'status': 'passwords not match'})
            user.set_password(password)
            user.save()
            return Response({'status': 'success'})
        else:
            return Response({'status': 'error'})
    