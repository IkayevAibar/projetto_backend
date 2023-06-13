import hashlib
import requests
import random
import string
import urllib.parse
import xmltodict


from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError


from drf_yasg.utils import swagger_auto_schema

from ..models import Order, TransactionResponce, TransactionPayment, TransactionStatus, TransactionCancel, TransactionRevoke
from ..serializers.transaction_serializers import  TransactionPaymentSerializer, TransactionStatusSerializer, TransactionCancelSerializer,\
                           TransactionRevokeSerializer,TransactionResponceSerializer

from app.settings import account_sid, auth_token, verify_sid, payment_get, payment_give

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = TransactionResponce.objects.all()
    http_method_names = ['get','post']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.action == 'status':
            return TransactionStatus.objects.all()
        elif self.action == 'cancel':
            return TransactionCancel.objects.all()
        elif self.action == 'revoke':
            return TransactionRevoke.objects.all()
        elif self.action == 'payment' or self.action == 'get_payment':
            return TransactionPayment.objects.all()

        return TransactionResponce.objects.all()

    def get_serializer_class(self):
        if self.action == 'status':
            return TransactionStatusSerializer
        elif self.action == 'cancel':
            return TransactionCancelSerializer
        elif self.action == 'revoke':
            return TransactionRevokeSerializer
        elif self.action == 'payment' or self.action == 'get_payment':
            return TransactionPaymentSerializer

        return TransactionResponceSerializer

    
    # @action(detail=False, methods=['get'])
    # def get_payment(self, request, *args, **kwargs):
    #     queryset = self.filter_queryset(self.get_queryset())

    #     page = self.paginate_queryset(queryset)
    #     if page is not None:
    #         serializer = self.get_serializer(page, many=True)
    #         return self.get_paginated_response(serializer.data)

    #     serializer = self.get_serializer(queryset, many=True)
    #     return Response(serializer.data)


    @swagger_auto_schema(
        request_body=TransactionPaymentSerializer
    )
    @action(detail=False, methods=['post'])
    def payment(self, request):
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

        pg_salt = self.generate_salt(16)  # Уникальная случайная строка для каждого запроса

        transaction_data['pg_salt'] = pg_salt
        
        secret_key = payment_get

        pg_sig = self.generate_signature(script_name, transaction_data, secret_key)
        
        transaction_data['pg_sig'] = pg_sig
        transaction_payment = TransactionPayment.objects.create(**transaction_data)
        transaction_payment.save()
        
        payload = {**transaction_data, 'pg_sig': pg_sig}

        try:
            response = requests.post(url, data=payload)
            try:
                xml_dict = xmltodict.parse(response.text)
                response_data = xml_dict['response']
            except xmltodict.ExpatError as e:
                return Response({'error': str(e)})

            if response_data['pg_status'] != 'ok':
                responce_status = status.HTTP_400_BAD_REQUEST
            else:
                responce_status = status.HTTP_200_OK
            
            transaction = self.save_transaction_responce(order=order, payload=response_data, script_name=script_name, transaction_id=transaction_payment.id)
            transaction.save()
               
            return Response({'responce' : response_data, 'transaction': transaction.id}, status=responce_status)

        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)})
    
    @action(detail=False, methods=['post'])
    def status(self, request):
        url = "https://api.paybox.money/get_status.php"

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

        pg_salt = self.generate_salt(16)  # Уникальная случайная строка для каждого запроса

        transaction_data['pg_salt'] = pg_salt
        
        secret_key = payment_get

        pg_sig = self.generate_signature(script_name, transaction_data, secret_key)
        
        transaction_data['pg_sig'] = pg_sig
        transaction_payment = TransactionStatus.objects.create(**transaction_data)
        transaction_payment.save()
        
        payload = {**transaction_data, 'pg_sig': pg_sig}

        try:
            response = requests.post(url, data=payload)
            try:
                xml_dict = xmltodict.parse(response.text)
                response_data = xml_dict['response']
            except xmltodict.ExpatError as e:
                return Response({'error': str(e)})

            if response_data['pg_status'] != 'ok':
                responce_status = status.HTTP_400_BAD_REQUEST
            else:
                responce_status = status.HTTP_200_OK
            
            transaction = self.save_transaction_responce(order=order, payload=response_data, script_name=script_name, transaction_id=transaction_payment.id)
            transaction.save()
               
            return Response({'responce' : response_data, 'transaction': transaction.id}, status=responce_status)

        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)})
    
    @action(detail=False, methods=['post'])
    def cancel(self, request):
        url = "https://api.paybox.money/cancel.php"

        script_name = urllib.parse.urlparse(url).path.split('/')[-1]
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        transaction_data = serializer.validated_data
        
        transaction_data['pg_merchant_id'] = '548856'

        pg_salt = self.generate_salt(16)  # Уникальная случайная строка для каждого запроса

        transaction_data['pg_salt'] = pg_salt
        
        secret_key = payment_get

        pg_sig = self.generate_signature(script_name, transaction_data, secret_key)
        
        transaction_data['pg_sig'] = pg_sig
        transaction_payment = TransactionCancel.objects.create(**transaction_data)
        transaction_payment.save()
        
        payload = {**transaction_data, 'pg_sig': pg_sig}

        try:
            response = requests.post(url, data=payload)
            try:
                xml_dict = xmltodict.parse(response.text)
                response_data = xml_dict['response']
            except xmltodict.ExpatError as e:
                return Response({'error': str(e)})

            if response_data['pg_status'] != 'ok':
                responce_status = status.HTTP_400_BAD_REQUEST
            else:
                responce_status = status.HTTP_200_OK
            
            transaction = self.save_transaction_responce(order=None, payload=response_data, script_name=script_name, transaction_id=transaction_payment.id)
            transaction.save()
               
            return Response({'responce' : response_data, 'transaction': transaction.id}, status=responce_status)

        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)})
    
    @action(detail=False, methods=['post'])
    def revoke(self, request):
        url = "https://api.paybox.money/revoke.php"

        script_name = urllib.parse.urlparse(url).path.split('/')[-1]
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        transaction_data = serializer.validated_data
        
        transaction_data['pg_merchant_id'] = '548856'
        transaction_data['pg_refund_amount'] = '0'

        pg_salt = self.generate_salt(16)  # Уникальная случайная строка для каждого запроса

        transaction_data['pg_salt'] = pg_salt
        
        secret_key = payment_get

        pg_sig = self.generate_signature(script_name, transaction_data, secret_key)
        
        transaction_data['pg_sig'] = pg_sig
        transaction_payment = TransactionRevoke.objects.create(**transaction_data)
        transaction_payment.save()
        
        payload = {**transaction_data, 'pg_sig': pg_sig}

        try:
            response = requests.post(url, data=payload)
            try:
                xml_dict = xmltodict.parse(response.text)
                response_data = xml_dict['response']
            except xmltodict.ExpatError as e:
                return Response({'error': str(e)})

            if response_data['pg_status'] != 'ok':
                responce_status = status.HTTP_400_BAD_REQUEST
            else:
                responce_status = status.HTTP_200_OK
            
            transaction = self.save_transaction_responce(order=None, payload=response_data, script_name=script_name, transaction_id=transaction_payment.id)
            transaction.save()
               
            return Response({'responce' : response_data, 'transaction': transaction.id}, status=responce_status)

        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)})
    
    def save_transaction_responce(self, order, payload, script_name, transaction_id):
        try:
            transactionResponce = TransactionResponce.objects.create(
                script_name=script_name,
                order=order,
                transaction_id=transaction_id,
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


