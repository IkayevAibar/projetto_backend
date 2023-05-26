import hashlib
import requests
import random
import string
import urllib.parse
import json
import xmltodict

from django.shortcuts import render

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenViewBase
from rest_framework.exceptions import ValidationError

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


from .permissions import IsAuthenticatedOrAdminOrReadOnly
from .models import User, Order, Transaction
from .serializers import UserSerializer, UserCreateSerializer, SendSMSRequestSerializer, VerifySMSRequestSerializer, \
                            TokenObtainPairSerializerWithoutPassword, TransactionSerializer, OrderSerializer, TransactionCreateSerializer
from app.settings import account_sid, auth_token, verify_sid, payment_get, payment_give

class TokenObtainPairWithoutPasswordView(TokenViewBase):
    serializer_class = TokenObtainPairSerializerWithoutPassword

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
        
        # Возврат базового сериализатора по умолчанию
        return UserSerializer
    def get_permissions(self):
        if self.action in ['create', 'send_sms', 'verify_sms']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticatedOrAdminOrReadOnly]
    
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

        try:
            user = User.objects.get(username=phone)
            serializer = self.get_serializer(user)

            if user.check_password(''):
                serializer.data['empty_password'] = True
            else:
                serializer.data['empty_password'] = False

            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({'detail': 'Пользователя с таким номер нет'}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        user_manager = User.objects
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data.get('username')
        password = serializer.validated_data.get('password')
        first_name = serializer.validated_data.get('first_name')
        sms_verified = serializer.validated_data.get('sms_verified')
        
        if sms_verified == True:
            user = user_manager.create_user(username=username, password=password, sms_verified=sms_verified, first_name=first_name)
        else:
            if(password):
                user = user_manager.create_user(username=username, password=password, sms_verified=sms_verified, first_name=first_name)
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

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    http_method_names = ['get', 'post', 'put', 'patch']

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    http_method_names = ['get', 'post']
    permission_classes = [AllowAny]

    # напиши get_serializer_class   
    def get_serializer_class(self):
        if self.action == 'payment':
            return TransactionCreateSerializer
        return TransactionSerializer
    
    @staticmethod
    def generate_salt(length):
        letters_and_digits = string.ascii_letters + string.digits
        return ''.join(random.choice(letters_and_digits) for i in range(length))

    @staticmethod
    def generate_signature(params, salt):
        pass
        # напиши генерацию сигнатуры docs.paybox.money

    @swagger_auto_schema(
        request_body=TransactionCreateSerializer
    )
    @action(detail=False, methods=['post'])
    def payment(self, request):
        url = "https://api.paybox.money/g2g/payment"
        script_name = urllib.parse.urlparse(url).path.split('/')[-1]
        
        order_id = int(request.data.get('order_id'))

        order: Order = Order.objects.get(pk=order_id)

        pg_amount = order.flat_layout.price
        pg_currency = 'KZT'
        pg_description = f'Order #{order.id}'

        pg_merchant_id = '548856'
        pg_card_name = request.data.get('pg_card_name')#'TEST TESTOV'
        pg_card_pan = request.data.get('pg_card_pan')#'4563960122001999'
        pg_card_cvc = request.data.get('pg_card_cvc')#'123'
        pg_card_month = request.data.get('pg_card_month')#'12'
        pg_card_year = request.data.get('pg_card_year')#'24'

        pg_auto_clearing = request.data.get('pg_auto_clearing')#'1'
        pg_testing_mode = request.data.get('pg_testing_mode')#'1'
        pg_result_url = request.data.get('pg_result_url')#'projetto.dev.factory.kz'
        pg_3ds_challenge = request.data.get('pg_3ds_challenge')#'0'
        pg_param1 = request.data.get('pg_param1')#''
        pg_param2 = request.data.get('pg_param2')#''
        pg_param3 = request.data.get('pg_param3')#''
        pg_order_id = order_id # Уникальный идентификатор заказа для каждого запроса

        pg_salt = self.generate_salt(16)  # Уникальная случайная строка для каждого запроса

        # pg_sig = self.generate_signature(pg_merchant_id, pg_amount, pg_currency, pg_salt)

        secret_key = payment_get

        data = {
            'pg_amount': pg_amount,
            'pg_currency': pg_currency,
            'pg_description': pg_description,
            'pg_merchant_id': pg_merchant_id,
            'pg_order_id': pg_order_id,
            'pg_card_name': pg_card_name,
            'pg_card_pan': pg_card_pan,
            'pg_card_cvc': pg_card_cvc,
            'pg_card_month': pg_card_month,
            'pg_card_year': pg_card_year,
            'pg_auto_clearing': pg_auto_clearing,
            'pg_testing_mode': pg_testing_mode,
            'pg_result_url': pg_result_url,
            'pg_3ds_challenge': pg_3ds_challenge,
            'pg_param1': pg_param1,
            'pg_param2': pg_param2,
            'pg_param3': pg_param3,
            'pg_salt': pg_salt
        }

        sorted_data = sorted(data.items(), key=lambda x: x[0])

        # Формирование строки для подписи
        data_string = ';'.join([f"{value}" for key, value in sorted_data])

        # Формирование строки для подписи с добавлением секретного ключа
        data_with_secret_key = f"{script_name};{data_string};{secret_key}"
        data_with_secret_key_encoded = data_with_secret_key.encode('latin-1')

        md5_hash = hashlib.md5(data_with_secret_key_encoded)
        pg_sig = md5_hash.hexdigest()

        payload = {**data, 'pg_sig': pg_sig}

        try:
            response = requests.post(url, data=payload)
            # if response.status_code != 200:
            #     return Response(response.text, status=status.HTTP_400_BAD_REQUEST)
            try:
                xml_dict = xmltodict.parse(response.text)
                response_data = xml_dict['response']
                print(response_data)
            except xmltodict.ExpatError as e:
                # Обработка ошибки ExpatError
                return Response({'error': str(e)})

            if response_data['pg_status'] != 'ok':
                responce_status = status.HTTP_400_BAD_REQUEST

                transaction = Transaction.objects.create(
                    script_name=script_name,
                    order=order,
                    status=response_data['pg_status'],
                    description=response_data['pg_error_description'])
            else:
                responce_status = status.HTTP_200_OK

                transaction = Transaction.objects.create(
                    script_name=script_name,
                    order=order,
                    status=response_data['pg_status'],
                    description=response_data['pg_description'],
                    pg_payment_id=response_data['pg_payment_id'],
                    pg_3ds=response_data['pg_3ds'],
                    pg_3d_acsurl=response_data['pg_3d_acsurl'],
                    pg_3d_md=response_data['pg_3d_md'],
                    pg_3d_pareq=response_data['pg_3d_pareq'],
                    pg_recurring_profile=response_data['pg_recurring_profile'],
                    pg_card_id=response_data['pg_card_id'],
                    pg_card_token=response_data['pg_card_token'],
                    pg_auth_code=response_data['pg_auth_code'],
                    pg_salt=response_data['pg_salt'],
                    pg_sig=response_data['pg_sig'],
                    pg_datetime=response_data['pg_datetime']
                    )
               
            return Response({'responce' : response_data, 'transaction': transaction.id}, status=responce_status)

        except requests.exceptions.RequestException as e:
            # Обработка ошибки RequestException
            return Response({'error': str(e)})
