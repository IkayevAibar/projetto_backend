import hashlib
import requests
import random
import string
import urllib.parse
import json
import xmltodict
import asyncio

from django.shortcuts import render
from django.http import HttpResponse

from asgiref.sync import sync_to_async
from celery.result import AsyncResult

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

from .tasks import start_task
from .permissions import IsAuthenticatedOrAdminOrReadOnly
from .models import User, Order, TransactionResponce, TransactionPayment, TransactionStatus, TransactionCancel, TransactionRevoke
from .serializers import  UserSerializer, UserCreateSerializer, SendSMSRequestSerializer, VerifySMSRequestSerializer, \
                            TokenObtainPairSerializerWithoutPassword, OrderSerializer, TransactionPaymentSerializer, \
                            TransactionStatusSerializer, TransactionCancelSerializer, TransactionRevokeSerializer, \
                            TransactionResponceSerializer
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

    @action(detail=True, methods=['get'], permission_classes = [AllowAny])
    def generate_pdf(self, request, pk=None):
        if pk is None:
            return Response({'message': "order id is required"})

        try:
            int(pk)
        except:
            return Response({'message': "order id must be a number"})

        order = self.queryset.get(pk=pk)

        result = start_task.delay(order.id)
        
        return Response({
            'message': "pdf is generating",
            'task_id': result.id,
            'check_pdf_status': f'http://projetto.dev.thefactory.kz/orders/{order.id}/check_pdf_status/?task_id={result.id}'
            })
    
    @action(detail=True, methods=['get'], permission_classes = [AllowAny])
    def check_pdf_status(self, request, pk=None):
        task_id = request.query_params.get('task_id')

        if task_id is None:
            return Response({'message': "task_id is required"})


        task = AsyncResult(task_id)
        if task.state == 'SUCCESS':
            return Response({'message': "pdf is ready", 'url': task.result})
        elif task.state == 'FAILURE':
            return Response({'message': "pdf generating is failed"})
        else:
            return Response({'message': "pdf is generating"})
    

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionResponceSerializer
    queryset = TransactionResponce.objects.all()
    http_method_names = ['get']
    permission_classes = [AllowAny]


class TransactionPaymentViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionPaymentSerializer
    queryset = TransactionPayment.objects.all()
    http_method_names = ['get','post']
    permission_classes = [AllowAny]

    def save_transaction_responce(self, order, payload, script_name):
        try:
            
                        
            transactionResponce = TransactionResponce.objects.create(
                script_name=script_name,
                order=order,
                #payment
                pg_status=payload.get('pg_status'),
                pg_description=payload.get('pg_description'),
                pg_payment_id=payload.get('pg_payment_id'),
                pg_redirect_url=payload.get('pg_redirect_url'),
                pg_redirect_url_type=payload.get('pg_redirect_url_type'),
                pg_redirect_qr=payload.get('pg_redirect_qr'),
                #status
                pg_transaction_status=payload.get('pg_transaction_status'),
                pg_testing_mode=payload.get('pg_testing_mode'),
                pg_create_date=payload.get('pg_create_date'),
                pg_can_reject=payload.get('pg_can_reject'),
                pg_captured=payload.get('pg_captured'),
                pg_card_pan=payload.get('pg_card_pan'),
                pg_card_id=payload.get('pg_card_id'),
                pg_card_token=payload.get('pg_card_token'),
                pg_card_hash=payload.get('pg_card_hash'),
                pg_failure_code=payload.get('pg_failure_code'),
                pg_failure_description=payload.get('pg_failure_description'),
                #cancel and revoke
                pg_error_code=payload.get('pg_error_code'),
                pg_error_description=payload.get('pg_error_description'),
                #for all
                pg_salt=payload.get('pg_salt'),
                pg_sig=payload.get('pg_sig'),
            )

            transactionResponce.save()

            return transactionResponce
        except Exception as e:
            pass

    @staticmethod
    def generate_salt(length):
        letters_and_digits = string.ascii_letters + string.digits
        return ''.join(random.choice(letters_and_digits) for i in range(length))

    @staticmethod
    def generate_signature(script_name, data, secret_key):
        sorted_data = sorted(data.items(), key=lambda x: x[0])

        # Формирование строки для подписи
        data_string = ';'.join([f"{value}" for key, value in sorted_data])

        # Формирование строки для подписи с добавлением секретного ключа
        data_with_secret_key = f"{script_name};{data_string};{secret_key}"
        data_with_secret_key_encoded = data_with_secret_key.encode('utf-8')

        md5_hash = hashlib.md5(data_with_secret_key_encoded)
        pg_sig = md5_hash.hexdigest()
        return pg_sig

    @swagger_auto_schema(
        request_body=TransactionPaymentSerializer
    )
    # @action(detail=False, methods=['post'])
    def create(self, request):
        url = "https://api.paybox.money/init_payment.php"

        script_name = urllib.parse.urlparse(url).path.split('/')[-1]
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)


        transaction_data = serializer.validated_data

        
        order_id = transaction_data.get('pg_order_id')
        order = None
        
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
            except:
                raise ValidationError('Заказ не найден')

        transaction_data['pg_merchant_id'] = '548856'
        transaction_data['pg_amount'] = order.flat_layout.price
        transaction_data['pg_currency'] = 'KZT'
        transaction_data['pg_testing_mode'] = '1'

        # Создание нового объекта Transaction на основе валидированных данных
        
        pg_salt = self.generate_salt(16)  # Уникальная случайная строка для каждого запроса

        transaction_data['pg_salt'] = pg_salt

        
        # pg_sig = self.generate_signature(pg_merchant_id, pg_amount, pg_currency, pg_salt)

        secret_key = payment_get

        # del transaction_data['pg_sig']

        pg_sig = self.generate_signature(script_name, transaction_data, secret_key)
        
        transaction_data['pg_sig'] = pg_sig

        transaction_payment = TransactionPayment.objects.create(**transaction_data)
        transaction_payment.save()
        
        print(transaction_data)
        payload = {**transaction_data, 'pg_sig': pg_sig}

        

        try:
            response = requests.post(url, data=payload)
            try:
                xml_dict = xmltodict.parse(response.text)
                response_data = xml_dict['response']
            except xmltodict.ExpatError as e:
                # Обработка ошибки ExpatError
                return Response({'error': str(e)})

            if response_data['pg_status'] != 'ok':
                responce_status = status.HTTP_400_BAD_REQUEST
            else:
                responce_status = status.HTTP_200_OK

            
            
            transaction = self.save_transaction_responce(order=order, payload=response_data, script_name=script_name)
            transaction.save()
            
               
            return Response({'responce' : response_data, 'transaction': transaction.id}, status=responce_status)

        except requests.exceptions.RequestException as e:
            # Обработка ошибки RequestException
            return Response({'error': str(e)})
    
    
    
    # @action(detail=False, methods=['post'])
    # def status(self, request):
    #     url = "https://api.paybox.money/g2g/status_v2"

    #     script_name = urllib.parse.urlparse(url).path.split('/')[-1]
    #     secret_key = payment_get
    #     pg_salt = self.generate_salt(16)  # Уникальная случайная строка для каждого запроса

    #     order_id = request.data.get('pg_order_id')

    #     if order_id:
    #         try:
    #             order = Order.objects.get(pk=int(order_id))
    #         except (ValueError, Order.DoesNotExist):
    #             return Response({'message':"Order not found"},status=status.HTTP_404_NOT_FOUND)
    #     else:
    #         order = None
        
    #     pg_payment_id = request.data.get('pg_payment_id')
    #     pg_merchant_id = '548856'

    #     data = {
    #         'pg_payment_id': pg_payment_id,
    #         'pg_merchant_id': pg_merchant_id,
    #         'pg_salt': pg_salt,
    #         'pg_order_id': order_id,
    #     }

    #     pg_sig = self.generate_signature(script_name, data, secret_key)

    #     payload = {**data, 'pg_sig': pg_sig}

    #     self.save_transaction_in(None, payload, script_name)

    #     try:
    #         response = requests.post(url, data=payload)
    #         try:
    #             xml_dict = xmltodict.parse(response.text)
    #             response_data = xml_dict['response']
    #             print(response_data)
    #         except xmltodict.ExpatError as e:
    #             # Обработка ошибки ExpatError
    #             return Response({'error': str(e)})

    #         if response_data['pg_status'] != 'ok':
    #             responce_status = status.HTTP_400_BAD_REQUEST

    #             transaction = Transaction.objects.create(
    #                 script_name=script_name,
    #                 order=order,
    #                 pg_payment_id=pg_payment_id,
    #                 status=response_data['pg_status'],
    #                 description=response_data['pg_error_description'].encode('latin-1').decode('utf-8'),
    #                 pg_error_code=response_data['pg_error_code']
    #                 )
    #         else:
    #             responce_status = status.HTTP_200_OK

    #             transaction = Transaction.objects.create(
    #                 script_name=script_name,
    #                 status=response_data['pg_status'],
    #                 pg_payment_id=response_data['pg_payment_id'],
    #                 pg_order_id=response_data['pg_order_id'],
    #                 pg_currency=response_data['pg_currency'],
    #                 pg_status=response_data['pg_status'],
    #                 pg_payment_status=response_data['pg_payment_status'],
    #                 pg_amount=response_data['pg_amount'],
    #                 pg_net_amount=response_data['pg_net_amount'],
    #                 pg_clearing_amount=response_data['pg_clearing_amount'],
    #                 pg_refund_amount=response_data['pg_refund_amount'],
    #                 pg_user_email=response_data['pg_user_email'],
    #                 pg_card_name=response_data['pg_card_name'],
    #                 pg_card_id=response_data['pg_card_id'],
    #                 pg_card_token=response_data['pg_card_token'],
    #                 pg_card_pan=response_data['pg_card_pan'],
    #                 pg_card_exp=response_data['pg_card_exp'],
    #                 pg_card_brand=response_data['pg_card_brand'],
    #                 pg_user_phone=response_data['pg_user_phone'],
    #                 pg_payment_date=response_data['pg_payment_date'],
    #                 pg_captured=response_data['pg_captured'],
    #                 pg_refund_payments=response_data['pg_refund_payments'],
    #                 pg_revoked_payments=response_data['pg_revoked_payments'],
    #                 pg_reference=response_data['pg_reference'],
    #                 pg_intreference=response_data['pg_intreference'],
    #                 pg_failure_code=response_data['pg_failure_code'],
    #                 pg_failure_description=response_data['pg_failure_description'],
    #                 pg_auth_code=response_data['pg_auth_code'],
    #                 pg_salt=response_data['pg_salt'],
    #                 pg_sig=response_data['pg_sig'],
    #                 pg_datetime=response_data['pg_datetime']
    #                 )
               
    #         return Response({'responce' : response_data, 'transaction': transaction.id}, status=responce_status)

    #     except requests.exceptions.RequestException as e:
    #         # Обработка ошибки RequestException
    #         return Response({'error': str(e)})

    # @action(detail=False, methods=['post'])
    # def cancel(self, request):
    #     url = "https://api.paybox.money/g2g/cancel"

    #     script_name = urllib.parse.urlparse(url).path.split('/')[-1]
    #     secret_key = payment_get
    #     pg_salt = self.generate_salt(16)  # Уникальная случайная строка для каждого запроса

    #     pg_payment_id = request.data.get('pg_payment_id')

    #     pg_merchant_id = '548856'

    #     data = {
    #         'pg_payment_id': pg_payment_id,
    #         'pg_merchant_id': pg_merchant_id,
    #         'pg_salt': pg_salt,
    #     }

    #     pg_sig = self.generate_signature(script_name, data, secret_key)

    #     payload = {**data, 'pg_sig': pg_sig}

    #     self.save_transaction_in(None, payload, script_name)

    #     try:
    #         response = requests.post(url, data=payload)
    #         try:
    #             xml_dict = xmltodict.parse(response.text)
    #             response_data = xml_dict['response']
    #             print(response_data)
    #         except xmltodict.ExpatError as e:
    #             # Обработка ошибки ExpatError
    #             return Response({'error': str(e)})

    #         if response_data['pg_status'] != 'ok':
    #             responce_status = status.HTTP_400_BAD_REQUEST

    #             transaction = Transaction.objects.create(
    #                 script_name=script_name,
    #                 pg_payment_id=pg_payment_id,
    #                 status=response_data['pg_status'],
    #                 description=response_data['pg_error_description'],
    #                 pg_error_code=response_data['pg_error_code']
    #                 )
    #         else:
    #             responce_status = status.HTTP_200_OK

    #             transaction = Transaction.objects.create(
    #                 script_name=script_name,
    #                 status=response_data['pg_status'],
    #                 pg_payment_id=response_data['pg_payment_id'],
    #                 pg_payment_revoke_id=response_data['pg_payment_revoke_id'],
    #                 pg_status=response_data['pg_status'],
    #                 pg_revoke_status=response_data['pg_revoke_status'],
    #                 pg_salt=response_data['pg_salt'],
    #                 pg_sig=response_data['pg_sig'],
    #                 pg_datetime=response_data['pg_datetime']
    #                 )
               
    #         return Response({'responce' : response_data, 'transaction': transaction.id}, status=responce_status)

    #     except requests.exceptions.RequestException as e:
    #         # Обработка ошибки RequestException
    #         return Response({'error': str(e)})
    
    # @action(detail=False, methods=['post'])
    # def revoke(self, request):
    #     url = "https://api.paybox.money/g2g/refund"

    #     script_name = urllib.parse.urlparse(url).path.split('/')[-1]
    #     secret_key = payment_get
    #     pg_salt = self.generate_salt(16)  # Уникальная случайная строка для каждого запроса

    #     order_id = request.data.get('order_id')
    #     pg_payment_id = request.data.get('pg_payment_id')
    #     if order_id:
    #         try:
    #             order = Order.objects.get(pk=int(order_id))
    #         except (ValueError, Order.DoesNotExist):
    #             return Response({'message':"Order not found"},status=status.HTTP_404_NOT_FOUND)
    #     else:
    #         raise ValidationError("Order id is required")
        
    #     pg_merchant_id = '548856'

    #     data = {
    #         'pg_payment_id': pg_payment_id,
    #         'pg_merchant_id': pg_merchant_id,
    #         'pg_amount': order.flat_layout.price,
    #         'pg_currency': "KZT",
    #         'pg_salt': pg_salt,
    #     }

    #     pg_sig = self.generate_signature(script_name, data, secret_key)

    #     payload = {**data, 'pg_sig': pg_sig}

    #     self.save_transaction_in(None, payload, script_name)

    #     try:
    #         response = requests.post(url, data=payload)
    #         try:
    #             xml_dict = xmltodict.parse(response.text)
    #             response_data = xml_dict['response']
    #             print(response_data)
    #         except xmltodict.ExpatError as e:
    #             # Обработка ошибки ExpatError
    #             return Response({'error': str(e)})

    #         if response_data['pg_status'] != 'ok':
    #             responce_status = status.HTTP_400_BAD_REQUEST

    #             transaction = Transaction.objects.create(
    #                 script_name=script_name,
    #                 pg_payment_id=pg_payment_id,
    #                 status=response_data['pg_status'],
    #                 description=response_data['pg_error_description'],
    #                 pg_error_code=response_data['pg_error_code']
    #                 )
    #         else:
    #             responce_status = status.HTTP_200_OK

    #             transaction = Transaction.objects.create(
    #                 script_name=script_name,
    #                 status=response_data['pg_status'],
    #                 pg_payment_id=response_data['pg_payment_id'],
    #                 pg_payment_refund_id=response_data['pg_payment_refund_id'],
    #                 pg_status=response_data['pg_status'],
    #                 pg_refund_status=response_data['pg_refund_status'],
    #                 pg_salt=response_data['pg_salt'],
    #                 pg_sig=response_data['pg_sig'],
    #                 pg_datetime=response_data['pg_datetime']
    #                 )
               
    #         return Response({'responce' : response_data, 'transaction': transaction.id}, status=responce_status)

    #     except requests.exceptions.RequestException as e:
    #         # Обработка ошибки RequestException
    #         return Response({'error': str(e)})

