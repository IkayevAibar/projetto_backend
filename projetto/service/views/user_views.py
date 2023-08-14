
from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from service.models import User, Order, SMSMessage
from service.serializers.user_serializers import  ChangePasswordSerializer, UserSerializer, UserCreateSerializer, \
                                                SendSMSRequestSerializer, VerifySMSRequestSerializer, UserListSerializer, SetPasswordSerializer
from service.serializers.order_serializers import OrderSerializer

from app.settings import account_sid, auth_token, verify_sid, sms_acc_sid_prod, sms_acc_pass_prod, sms_version_type

from .sms_views import send_sms, generate_code

class UserViewSet(mixins.UpdateModelMixin,
                   mixins.RetrieveModelMixin, 
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in 'send_sms_to_phone':
            return SendSMSRequestSerializer
        elif self.action in 'verify_sms_and_authorization':
            return VerifySMSRequestSerializer
        elif self.action in 'restore_password':
            return ChangePasswordSerializer
        elif self.action in 'list':
            return UserListSerializer
        elif self.action in 'set_password':
            return SetPasswordSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'send_sms_to_phone', 'verify_sms_and_authorization', 'restore_password']:
            permission_classes = [AllowAny]
        elif self.action in ['list', 'retrieve', 'update', 'partial_update', 'destroy', 'get_all_orders']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
    
        return [permission() for permission in permission_classes]
    
    @staticmethod
    def get_or_create_user(phone_number):
        user = None
        try:
            user = User.objects.get(username=phone_number)
        except User.DoesNotExist:
            pass
        
        if(user):
            empty_password = user.check_password('')
            user_status = {'user_status': "already exist", 'user_id': user.id, 'empty_password': empty_password}
        else:
            # Создание нового пользователя, если он не существует
            print("Создание нового пользователя")
            print(phone_number)
            user = User.objects.create_user(username=phone_number, sms_verified=True)
            user_status = {'user_status': "created", 'user_id': user.id}
        # Генерация токена
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        return {'user': user_status, 'access_token': access_token, 'refresh_token': refresh_token}

    @swagger_auto_schema(
        request_body=VerifySMSRequestSerializer,
        operation_description='Потверждение номера телефона и регистрация пользователя',
    )
    @action(detail=False, methods=['post'], permission_classes = [AllowAny])
    def verify_sms_and_authorization(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        verified_number = serializer.validated_data.get('phone_number')
        otp_code = serializer.validated_data.get('otp_code')

        if(sms_version_type == "PROD"):
            recipient = verified_number
            code = otp_code

            try:
                sms_message = SMSMessage.objects.get(phone=recipient, code=code, sms_status='sent')
                sms_message.sms_status = "success"
                sms_message.save()

                user_response = self.get_or_create_user(recipient)
                return Response({'success': True, 'message': 'Код подтвержден', 'user': user_response})
            except SMSMessage.DoesNotExist:
                return Response({'success': False, 'message': 'Неверный код подтверждения'})
        else:
            client = Client(account_sid, auth_token)

            try:
                verification_check = client.verify.v2.services(verify_sid) \
                    .verification_checks \
                    .create(to="+"+verified_number, code=otp_code)
            except TwilioRestException as e:
                return Response({'status':e.code})
            
            if verification_check.status == 'approved':
                # Аутентификация пользователя по номеру телефона
                
                user_response = self.get_or_create_user(verified_number)
                return Response({'status': verification_check.status, 'result': user_response})
            else:
                return Response({'status': verification_check.status})

    @swagger_auto_schema(
        request_body=SendSMSRequestSerializer,
        operation_description='Send SMS verification code to your phone number'
    )
    @action(detail=False, methods=['post'], permission_classes = [AllowAny])
    def send_sms_to_phone(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        verified_number = serializer.validated_data.get('phone_number')

        if(verified_number is None):
            return Response({'status': 'Номер телефона не указан'})

        if(sms_version_type == "PROD"):
            username = sms_acc_sid_prod
            password = sms_acc_pass_prod
            recipient = verified_number
            # Генерируем код
            code = generate_code()

            # Создаем текст сообщения
            message = f'Код для подтверждения регистрации Projetto.kz: {code}'

            if send_sms(username, password, recipient, message):
                # Отправка SMS прошла успешно
                # Сохраняем сообщение в базу данных
                SMSMessage.objects.create(phone=recipient, code=code, sms_status='sent')
                return Response({'success': True, 'message': 'SMS успешно отправлено'})
            else:
                # Ошибка при отправке SMS
                SMSMessage.objects.create(phone=recipient, code=code, sms_status='not_sent')
                return Response({'success': False, 'message': 'Не удалось отправить SMS'})
        else:
            client = Client(account_sid, auth_token)
            try:
                verification = client.verify.v2.services(verify_sid) \
                    .verifications \
                    .create(to="+"+verified_number, channel="sms", locale="ru")
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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data.get('phone')
        try:
            user = User.objects.get(username=phone)
        except User.DoesNotExist:
            return Response({'status': 'Пользователь c таким номерем не найден'})
        
        verified_number = user.username
        otp_code = serializer.validated_data.get('otp_code')
        client = Client(account_sid, auth_token)

        try:
            verification_check = client.verify.v2.services(verify_sid) \
                .verification_checks \
                .create(to=verified_number, code=otp_code)
        except TwilioRestException as e:
            return Response({'status':e.code})

        if verification_check.status == 'approved':
            password = serializer.validated_data.get('password')
            confirm_password = serializer.validated_data.get('confirm_password')
            if(password != confirm_password):
                return Response({'status': 'passwords not match'})
            user.set_password(password)
            user.save()
            return Response({'status': 'success'})
        else:
            return Response({'status': 'error'})
    
    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description='Password set successfully',
                examples={
                    'application/json': {
                        'status': 'success'
                    }
                }
            ),
            400: openapi.Response(
                description='Bad request',
                examples={
                    'application/json': {
                        'status': 'Пользователь с таким ID не найден или пароли не совпадают'
                    }
                }
            ),
        }
    )
    @action(detail=False, methods=['post'])
    def set_password(self, request):
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = serializer.validated_data.get('user_id')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'status': 'Пользователь c таким ID не найден'})
        
        password = serializer.validated_data.get('password')
        confirm_password = serializer.validated_data.get('confirm_password')
        if(password != confirm_password):
            return Response({'status': 'passwords not match'})
        user.set_password(password)
        user.save()
        return Response({'status': 'success'})
