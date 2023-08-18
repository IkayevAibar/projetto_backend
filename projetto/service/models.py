from django.utils import timezone
from datetime import datetime

from django.db import models
from django.contrib.auth.models import AbstractUser,UserManager
from django.core.files.storage import default_storage
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from residence.models import Residence, Apartment, Layout, Cluster, Floor
from .managers import UserManager

import os

from PyPDF2 import PdfFileWriter, PdfFileReader
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A2
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

class Timestamp(models.Model):
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Изменено", auto_now=True)
    
    class Meta:
        abstract = True

class User(AbstractUser):
    first_name = None
    last_name = None
    email = None 
    sms_verified = models.BooleanField("SMS верифицирован", default= False)
    full_name = models.CharField("Полное имя", max_length=150, blank=True)
    
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
    apartment = models.ForeignKey("residence.Apartment", verbose_name="ID Квартиры", on_delete=models.CASCADE)
    cluster = models.ForeignKey("residence.Cluster", verbose_name="ID Кластера", on_delete=models.CASCADE)
    doc = models.FileField("Договор", upload_to='docs/',null=True, blank=True)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='created')
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Изменено", auto_now_add=True)

    @staticmethod
    def draw(can, text, x, y, font_size):
        can.setFont('OpenSans', font_size)
        can.setFillColorRGB(0.85, 0.85, 0.85)
        text_width = can.stringWidth(text, 'OpenSans', font_size)
        text_height = font_size
        y = y 
        x = x
        can.drawCentredString(x, y, text)

    
    def generate_doc(self):
        residence:Residence = self.cluster.residence_id
        cluster:Cluster = self.cluster
        apartment: Apartment = self.apartment
        layout: Layout = self.flat_layout

        current_year = datetime.now(tz=timezone.get_current_timezone()).year

        match apartment.room_number:
            case 1: room_count = "Однокомнатная квартира"
            case 2: room_count = "Двухкомнатная квартира"
            case 3: room_count = "Трёхкомнатная квартира"
            case 4: room_count = "Четырёхкомнатная квартира"
            case _: room_count = apartment.room_number + "-комнатная квартира"

        pdfmetrics.registerFont(TTFont('OpenSans', './utils/opensans.ttf'))

        packet = io.BytesIO()

        can = canvas.Canvas(packet, pagesize=A2)
        # can.rotate(90)

        self.draw(can, 'Рабочий проект дизайн интерьера',  600, 390, 24)
        self.draw(can, residence.title, 600, 325, 38)
        self.draw(can, room_count + ": " + f"{residence.slug}/{cluster.name}/{layout.room_number}.{layout.variant}/{layout.type_of_apartment}" , 600, 275, 28)
        self.draw(can, self.user.full_name, 975, 85, 24)
        
        can.save()

        packet.seek(0)

        new_pdf = PdfFileReader(packet)
        existing_pdf = PdfFileReader(open("./utils/projetto_titul.pdf", "rb"))
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


class Ticket(Timestamp):
    full_name = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    email = models.CharField(max_length=30, blank=True)
    description = models.TextField(max_length=1000, null=True, blank=True)

    class Meta:
        verbose_name = 'Тикет'
        verbose_name_plural = 'Тикеты'
        ordering = ['created_at']

class TicketAttachment(Timestamp):
    ticket = models.ForeignKey("Ticket", on_delete=models.CASCADE, blank=True)
    name = models.CharField(max_length=100, blank=True)
    file = models.FileField("Screenshot", upload_to='tickets/', blank=True)

    class Meta:
        verbose_name = 'Вложение для Тикета'
        verbose_name_plural = 'Вложении  для Тикета'


class SMSMessage(Timestamp):
    STATUS_SMS = (
        ('sent', 'Отправлено'),
        ('not_sent', 'Не отправлено'),
        ('success', 'Подтверждено')
    )
    sms_status = models.CharField(max_length=50, choices=STATUS_SMS, default="sent", blank=True)
    phone = models.CharField(max_length=15)
    code = models.CharField(max_length=4)

    def __str__(self):
        return f'SMS to {self.phone} - Code: {self.code}'

    class Meta:
        verbose_name = 'SMS сообщение'
        verbose_name_plural = 'SMS сообщения'
        ordering = ['-created_at']

# payload = {'pg_order_id': '123456789',
# 'pg_payment_id': '12345',
# 'pg_amount': '10',
# 'pg_currency': 'KZT',
# 'pg_ps_currency': 'KZT',
# 'pg_ps_amount': '5',
# 'pg_ps_full_amount': '5',
# 'Параметры мерчанта': '',
# 'pg_salt': 'some random string',
# 'pg_sig': '{{paybox_signature}}'}

class FreedomCheckRequest(Timestamp):
    pg_order_id = models.CharField(max_length=50, blank=True, null=True)
    pg_payment_id = models.CharField(max_length=50, blank=True, null=True)
    pg_amount = models.CharField(max_length=50, blank=True, null=True)
    pg_currency = models.CharField(max_length=50, blank=True, null=True)
    pg_ps_currency = models.CharField(max_length=50, blank=True, null=True)
    pg_ps_amount = models.CharField(max_length=50, blank=True, null=True)
    pg_ps_full_amount = models.CharField(max_length=50, blank=True, null=True)
    pg_salt = models.CharField(max_length=50, blank=True, null=True)
    pg_sig = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f'Freedom check request #{self.pk}'

    class Meta:
        verbose_name = 'Запрос на проверку платежа'
        verbose_name_plural = 'Запросы на проверку платежа'
        ordering = ['-created_at']

# payload = {
# 'pg_order_id': '123456789',
# 'pg_payment_id': '12345',
# 'pg_amount': '500',
# 'pg_currency': 'KZT',
# 'pg_net_amount': '482.5',
# 'pg_ps_amount': '500',
# 'pg_ps_full_amount': '500',
# 'pg_ps_currency': 'KZT',
# 'pg_description': 'Покупка в интернет магазине Site.kz',
# 'pg_result': '1',
# 'pg_payment_date': '2019-01-01 12:00:00',
# 'pg_can_reject': '1',
# 'pg_user_phone': '7077777777777',
# 'pg_user_contact_email': 'mail@customer.kz',
# 'pg_testing_mode': '1',
# 'pg_captured': '0',
# 'pg_card_pan': '5483-18XX-XXXX-0293',
# 'Параметры мерчанта': '',
# 'pg_salt': 'some random string',
# 'pg_sig': '{{paybox_signature}}',
# 'pg_payment_method': 'bankcard'
# }

class FreedomResultRequest(Timestamp):
    pg_order_id = models.CharField(max_length=50, blank=True, null=True)
    pg_payment_id = models.CharField(max_length=50, blank=True, null=True)
    pg_amount = models.CharField(max_length=50, blank=True, null=True)
    pg_currency = models.CharField(max_length=50, blank=True, null=True)
    pg_net_amount = models.CharField(max_length=50, blank=True, null=True)
    pg_ps_amount = models.CharField(max_length=50, blank=True, null=True)
    pg_ps_full_amount = models.CharField(max_length=50, blank=True, null=True)
    pg_ps_currency = models.CharField(max_length=50, blank=True, null=True)
    pg_description = models.CharField(max_length=50, blank=True, null=True)
    pg_result = models.CharField(max_length=50, blank=True, null=True)
    pg_payment_date = models.CharField(max_length=50, blank=True, null=True)
    pg_can_reject = models.CharField(max_length=50, blank=True, null=True)
    pg_user_phone = models.CharField(max_length=50, blank=True, null=True)
    pg_user_contact_email = models.CharField(max_length=50, blank=True, null=True)
    pg_testing_mode = models.CharField(max_length=50, blank=True, null=True)
    pg_captured = models.CharField(max_length=50, blank=True, null=True)
    pg_card_pan = models.CharField(max_length=50, blank=True, null=True)
    pg_salt = models.CharField(max_length=50, blank=True, null=True)
    pg_sig = models.CharField(max_length=50, blank=True, null=True)
    pg_payment_method = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f'Freedom result request #{self.pk}'

    class Meta:
        verbose_name = 'Запрос на результат платежа'
        verbose_name_plural = 'Запросы на результат платежа'
        ordering = ['-created_at']
