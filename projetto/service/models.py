from django.db import models
from django.contrib.auth.models import AbstractUser,UserManager as BaseUserAdmin
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from residence.models import Residence, Apartment
from .managers import UserManager

import os

from PyPDF2 import PdfFileWriter, PdfFileReader
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape, A3
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

class Timestamp(models.Model):
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Изменено", auto_now=True)
    
    class Meta:
        abstract = True


class User(AbstractUser):
    email = None 
    REQUIRED_FIELDS = []
    sms_verified = models.BooleanField("SMS верифицирован", default= False)

    objects = UserManager()

    def __str__(self):
        return "%d. %s" % (self.id, self.username)
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

class Order(models.Model):
    STATUS_CHOICES = (
        ('created', 'Создан'),
        ('paid', 'Оплачен'),
        ('canceled', 'Отменён'),
    )

    user = models.ForeignKey(User, verbose_name="ID Клиента", on_delete=models.CASCADE)
    flat_layout = models.ForeignKey("residence.Layout", verbose_name="ID Планировки", on_delete=models.CASCADE)
    doc = models.FileField("Договор", upload_to='docs/',null=True, blank=True)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='created')
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Изменено", auto_now_add=True)

    @staticmethod
    def draw(can, text, x, y, font_size, type="static"):
        print(text + " is drawing...")
        can.setFont('ArialUnicode', font_size)
        text_width = can.stringWidth(text, 'ArialUnicode', font_size)
        text_height = font_size
        y = y 
        if type == "dynamic":
            x = x
            can.drawCentredString(x, y, text)
        else:
            x = x - text_width
            can.drawString(x, y, text)

    
    def generate_doc(self):
        residence:Residence = self.flat_layout.apartment.floor.cluster.residence_id
        apartment: Apartment = self.flat_layout.apartment

        match apartment.room_number:
            case 1: room_count = "Однокомнатная квартира"
            case 2: room_count = "Двухкомнатная квартира"
            case 3: room_count = "Трёхкомнатная квартира"
            case 4: room_count = "Четырёхкомнатная квартира"
            case _: room_count = apartment.room_number + "-комнатная квартира"

        pdfmetrics.registerFont(TTFont('ArialUnicode', './utils/arial_unicode.ttf'))

        packet = io.BytesIO()

        can = canvas.Canvas(packet, pagesize=A3)
        can.rotate(90)

        self.draw(can, 'Рабочий проект дизайн интерьера', 775, -430, 24)
        self.draw(can, residence.title, 600, -525, 38, "dynamic")
        self.draw(can, room_count + ": " + "RT/01/08/1.1/def" , 600, -575, 28, "dynamic")
        self.draw(can, 'Владелец проекта:', 1100, -700, 24)
        self.draw(can, self.user.first_name, 975, -735, 24, "dynamic")
        self.draw(can, 'г.АЛМАТЫ 2023', 675, -775, 24)
        
        can.save()

        packet.seek(0)

        new_pdf = PdfFileReader(packet)
        existing_pdf = PdfFileReader(open("./utils/project_free.pdf", "rb"))
        output = PdfFileWriter()

        page = existing_pdf.pages[0]
        page.merge_page(new_pdf.pages[0])
        output.add_page(page)

        file_name = residence.title + ".pdf"
        file_path = os.path.join('docs', file_name)

        with default_storage.open(file_path, "wb") as file:
            output.write(file)

        self.doc.name = file_path
        self.save()

        return self.doc.url

    def __str__(self):
        return f"Заказ #{self.pk}"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

class TransactionResponce(Timestamp):
    script_name = models.CharField("Имя вызываемого скрипта (от последнего / до конца или ?)", max_length=200, blank=True, null=True)
    order = models.ForeignKey(Order, verbose_name="Заказ", on_delete=models.CASCADE, null=True, blank=True)

    #payment
    pg_status = models.CharField("Статус запроса", max_length=20) # ok, error
    pg_description = models.CharField("Описание статуса", max_length=200, blank=True, null=True)
    pg_payment_id = models.CharField("ID транзакции", max_length=200, blank=True, null=True)
    pg_redirect_url = models.CharField("URL для перехода на страницу оплаты", max_length=200, blank=True, null=True)
    pg_redirect_url_type = models.CharField("Тип перехода на страницу оплаты", max_length=200, blank=True, null=True)
    pg_redirect_qr = models.CharField("QR-код для перехода на страницу оплаты", max_length=200, blank=True, null=True)

    #status
    pg_transaction_status = models.CharField("Статус транзакции", max_length=200, blank=True, null=True) 
    '''
        Статус	    Описание
        ------------------------------------------------------
        partial	    Новый платеж
        pending	    Ожидание плательщика или платежной системы
        refunded	По платежу прошел возврат
        revoked	    По платежу прошла отмена
        ok	        Платеж успешно завершен
        failed	    Платеж в ошибке
        incomplete	Истекло время жизни платежа
    '''
    pg_testing_mode = models.CharField("Тестовый режим", max_length=200, blank=True, null=True) # 0 - платеж в боевом режиме 1 - платеж в тестовом режиме
    pg_create_date = models.CharField("Дата создания платежа", max_length=200, blank=True, null=True)
    pg_can_reject = models.CharField("Возможность отмены платежа", max_length=200, blank=True, null=True) # 0 - отмена платежа невозможна 1 - отмена платежа возможна
    pg_captured = models.CharField("Платеж подтвержден", max_length=200, blank=True, null=True) # 0 - платеж не подтвержден 1 - платеж подтвержден
    pg_card_pan = models.CharField("Маскированный Номер карты", max_length=200, blank=True, null=True)
    pg_card_id = models.CharField("Идентификатор карты", max_length=200, blank=True, null=True)
    pg_card_token = models.CharField("Токен карты", max_length=200, blank=True, null=True)
    pg_card_hash = models.CharField("Хэш карты", max_length=200, blank=True, null=True)
    pg_failure_code = models.CharField("Код ошибки", max_length=200, blank=True, null=True)
    pg_failure_description = models.CharField("Описание ошибки", max_length=200, blank=True, null=True)

    #cancel and revoke
    pg_error_code = models.CharField("Код ошибки", max_length=200, blank=True, null=True)
    pg_error_description = models.CharField("Описание ошибки", max_length=200, blank=True, null=True)

    #for all
    pg_salt = models.CharField("Случайная строка", max_length=200, blank=True, null=True)
    pg_sig = models.CharField("Цифровая подпись запроса", max_length=200, blank=True, null=True)

    def __str__(self):
        return f"Транзакция #{self.pk}"
    
    class Meta:
        verbose_name = "Транзакция"
        verbose_name_plural = "Транзакции"

class TransactionPayment(Timestamp):
    #required
    pg_order_id = models.CharField("ID заказа", max_length=200, blank=True, null=True)
    pg_merchant_id = models.CharField("ID магазина", max_length=200, blank=True, null=True)
    pg_amount = models.CharField("Сумма платежа", max_length=200, blank=True, null=True)
    pg_description = models.TextField("Описание", blank=True, null=True)
    pg_salt = models.CharField("Случайная строка", max_length=200, blank=True, null=True)
    pg_sig = models.CharField("Цифровая подпись запроса", max_length=200, blank=True, null=True)
    # not required
    pg_currency = models.CharField("Валюта платежа/перевода", max_length=200, blank=True, null=True, default="KZT")
    pg_check_url = models.CharField("URL для проверки платежа", max_length=200, blank=True, null=True)
    pg_result_url = models.CharField("URL для сообщения о результате платежа", max_length=200, blank=True, null=True)
    pg_refund_url = models.CharField("URL для возврата платежа", max_length=200, blank=True, null=True)
    pg_request_method = models.CharField("Метод отправки данных", max_length=200, blank=True, null=True)
    pg_success_url = models.CharField("URL успешной оплаты", max_length=200, blank=True, null=True)
    pg_failure_url = models.CharField("URL неуспешной оплаты", max_length=200, blank=True, null=True)
    pg_success_url_method = models.CharField("Метод отправки данных для успешной оплаты", max_length=200, blank=True, null=True)
    pg_failure_url_method = models.CharField("Метод отправки данных для неуспешной оплаты", max_length=200, blank=True, null=True)
    pg_state_url = models.CharField("URL для получения статуса платежа", max_length=200, blank=True, null=True)
    pg_state_url_method = models.CharField("Метод отправки данных для получения статуса платежа", max_length=200, blank=True, null=True)
    pg_site_url = models.CharField("URL сайта", max_length=200, blank=True, null=True)
    pg_payment_system = models.CharField("Платежная система", max_length=200, blank=True, null=True)
    pg_lifetime = models.CharField("Время жизни счета", max_length=200, blank=True, null=True)
    pg_user_phone = models.CharField("Телефон пользователя в системе продавца", max_length=200, blank=True, null=True)
    pg_user_contact_email = models.CharField("Email пользователя в системе продавца", max_length=200, blank=True, null=True)
    pg_user_ip = models.CharField("IP пользователя в системе продавца", max_length=200, blank=True, null=True)  
    pg_postpone_payment = models.CharField("Отложенный платеж", max_length=200, blank=True, null=True)  # 1 - отложенный платеж, 0 - обычный платеж
    pg_language = models.CharField("Язык платежной страницы", max_length=200, blank=True, null=True)
    pg_testing_mode = models.CharField("Тестовый режим", max_length=200, blank=True, null=True) # 1 - тестовый режим, 0 - боевой режим
    pg_user_id = models.CharField("ID пользователя в системе продавца", max_length=200, blank=True, null=True)
    pg_recurring_start = models.CharField("Дата начала рекуррентных платежей", max_length=200, blank=True, null=True)
    pg_recurring_lifetime = models.CharField("Время жизни рекуррентных платежей", max_length=200, blank=True, null=True)
    # pg_receipt_positions = models.CharField("Позиции чека", max_length=200, blank=True, null=True)
    pg_param1 = models.CharField("Дополнительный параметр 1", max_length=200, blank=True, null=True)
    pg_param2 = models.CharField("Дополнительный параметр 2", max_length=200, blank=True, null=True)
    pg_param3 = models.CharField("Дополнительный параметр 3", max_length=200, blank=True, null=True)
    pg_auto_clearing = models.CharField("Автоматическая очистка платежей", max_length=200, blank=True, null=True)
    pg_payment_method = models.CharField("Способ оплаты", max_length=200, blank=True, null=True)
    '''
    pg_payment_method:
        wallet - Электронные деньги
        internetbank - Интернет-банкинг
        other - Терминалы
        bankcard - Банковские карты
        cash - Точки приема платежей
        mobile_commerce - Мобильная коммерция

    '''
    pg_timeout_after_payment = models.CharField("Время жизни счета после оплаты", max_length=200, blank=True, null=True)
    pg_generate_qr = models.CharField("Генерация QR-кода", max_length=200, blank=True, null=True) # 1 - генерация QR-кода, 0 - не генерировать QR-код
    pg_3ds_challenge = models.CharField("3DS Challenge", max_length=200, blank=True, null=True) 

    def __str__(self):
        return f"Платеж #{self.pk}"

    class Meta:
        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"

# class TransactionPaymentAcs(Timestamp):
#     # transaction = models.ForeignKey(Transaction, verbose_name="Транзакция", on_delete=models.CASCADE, null=True, blank=True)
#     # transaction = models.OneToOneField(Transaction, verbose_name="Транзакция", on_delete=models.CASCADE, null=True, blank=True)
#     pg_payment_id = models.CharField("ID транзакции", max_length=200, blank=True, null=True)
#     pg_payment_system = models.CharField("Платежная система", max_length=200, blank=True, null=True)
#     pg_amount = models.CharField("Сумма платежа", max_length=200, blank=True, null=True)
#     pg_currency = models.CharField("Валюта платежа/перевода", max_length=200, blank=True, null=True, default="KZT")
#     pg_card_number = models.CharField("Номер карты", max_length=200, blank=True, null=True)
#     pg_card_exp = models.CharField("Дата истечения срока карты", max_length=200, blank=True, null=True)
#     pg_card_name = models.CharField("Имя плательщика", max_length=200, blank=True, null=True)
#     pg_card_holder = models.CharField("Имя держателя карты", max_length=200, blank=True, null=True)
#     pg_card_type = models.CharField("Тип карты", max_length=200, blank=True, null=True)
#     pg_salt = models.CharField("Случайная строка", max_length=200, blank=True, null=True)
#     pg_sig = models.CharField("Цифровая подпись запроса", max_length=200, blank=True, null=True)


class TransactionStatus(Timestamp):
    pg_merchant_id = models.CharField("ID мерчанта", max_length=200, blank=True, null=True)
    pg_payment_id = models.CharField("ID транзакции", max_length=200, blank=True, null=True)
    pg_order_id = models.CharField("ID заказа", max_length=200, blank=True, null=True)
    pg_salt = models.CharField("Случайная строка", max_length=200, blank=True, null=True)
    pg_sig = models.CharField("Цифровая подпись запроса", max_length=200, blank=True, null=True)

    def __str__(self):
        return f"Статус транзакции #{self.pk}"
    
    class Meta:
        verbose_name = "Статус транзакции"
        verbose_name_plural = "Статусы транзакций"


class TransactionCancel(Timestamp):
    pg_merchant_id = models.CharField("ID мерчанта", max_length=200, blank=True, null=True)
    pg_payment_id = models.CharField("ID транзакции", max_length=200, blank=True, null=True)
    pg_salt = models.CharField("Случайная строка", max_length=200, blank=True, null=True)
    pg_sig = models.CharField("Цифровая подпись запроса", max_length=200, blank=True, null=True)

    def __str__(self):
        return f"Отмена транзакции #{self.pk}"
    
    class Meta:
        verbose_name = "Отмена транзакции"
        verbose_name_plural = "Отмены транзакций"

class TransactionRevoke(Timestamp):
    pg_merchant_id = models.CharField("ID мерчанта", max_length=200, blank=True, null=True)
    pg_payment_id = models.CharField("ID транзакции", max_length=200, blank=True, null=True)
    pg_refund_amount = models.CharField("Сумма возврата. ", max_length=200, blank=True, null=True ,help_text="Если параметр не передан или передан 0, то возвращается вся сумма")
    pg_salt = models.CharField("Случайная строка", max_length=200, blank=True, null=True)
    pg_sig = models.CharField("Цифровая подпись запроса", max_length=200, blank=True, null=True)

    def __str__(self):
        return f"Возврат транзакции #{self.pk}"
    
    class Meta:
        verbose_name = "Возврат транзакции"
        verbose_name_plural = "Возвраты транзакций"