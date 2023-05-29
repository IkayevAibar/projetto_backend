from django.db import models
from django.contrib.auth.models import AbstractUser,UserManager as BaseUserAdmin
from .managers import UserManager

# Create your models here.
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
    doc = models.FileField("Договор", upload_to='doc/',null=True, blank=True)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='created')
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Изменено", auto_now_add=True)

    def __str__(self):
        return f"Заказ #{self.pk}"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

class Transaction(models.Model):
    script_name = models.CharField("Имя вызываемого скрипта (от последнего / до конца или ?)", max_length=200, blank=True, null=True)
    order = models.ForeignKey(Order, verbose_name="Заказ", on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField("Статус запроса", max_length=20)
    description = models.TextField("Описание", blank=True, null=True)

    pg_error_code = models.CharField("ID кода ошибки", max_length=200, blank=True, null=True)

    pg_payment_id = models.CharField("ID транзакции", max_length=200, blank=True, null=True)
    pg_3ds = models.CharField("Флаг обозначающий необходимость запроса 3ds.", max_length=200, blank=True, null=True, help_text="1 – 3ds установлен, 0 - нет")
    pg_3d_acsurl = models.CharField("Url Банка эмитента карты для проверки 3ds", max_length=200, blank=True, null=True)
    pg_3d_md = models.CharField("Параметр для запроса 3ds", max_length=200, blank=True, null=True)
    pg_3d_pareq = models.CharField("Параметр для запроса 3ds", max_length=200, blank=True, null=True)
    pg_recurring_profile = models.CharField("ID рекуррентного профиля", max_length=200, blank=True, null=True)

    pg_card_name = models.CharField("Имя плательщика", max_length=200, blank=True, null=True)
    pg_card_id = models.CharField("ID сохраненной карты для следующих платежей (Deprecated)", max_length=200, blank=True, null=True)
    pg_card_token = models.CharField("Токен сохраненной карты для следующих платежей", max_length=200, blank=True, null=True)
    pg_card_pan = models.CharField("Маскированный номер карты (часть цифр номера карты скрыты).", max_length=200, blank=True, null=True)
    pg_card_exp = models.CharField("Дата истечения срока карты", max_length=200, blank=True, null=True)
    pg_card_brand = models.CharField("Код бренда карты", max_length=200, blank=True, null=True)
    pg_auth_code = models.CharField("Код авторизации платежа от банка", max_length=200, blank=True, null=True)

    pg_salt = models.CharField("Случайная строка", max_length=200, blank=True, null=True)
    pg_sig = models.CharField("Цифровая подпись запроса", max_length=200, blank=True, null=True)

    pg_payment_date = models.CharField("Дата платежа", max_length=200, blank=True, null=True)
    pg_datetime = models.CharField("Дата и время запроса", max_length=200, blank=True, null=True)

    pg_user_id = models.CharField("ID пользователя в системе продавца", max_length=200, blank=True, null=True)
    pg_user_email = models.CharField("Email пользователя в системе продавца", max_length=200, blank=True, null=True)
    pg_user_phone = models.CharField("Телефон пользователя в системе продавца", max_length=200, blank=True, null=True)
    pg_user_ip = models.CharField("IP пользователя в системе продавца", max_length=200, blank=True, null=True)

    pg_net_amount = models.CharField("Сумма выставленная в платеже за минусом комиссии", max_length=200, blank=True, null=True)
    pg_clearing_amount = models.CharField("Сумма, списанная при проведении клиринга платежа", max_length=200, blank=True, null=True)
    pg_captured = models.CharField("Флаг указывающий прошло ли списание (клиринг) по платежу", max_length=200, blank=True, null=True)
    pg_refund_amount = models.CharField("Возвращенная сумма", max_length=200, blank=True, null=True)
    pg_refund_payments = models.CharField("Список возвратов по данному платежу", max_length=2000, blank=True, null=True)
    pg_revoked_payments = models.CharField("Список отмен по данному платежу", max_length=2000, blank=True, null=True)
    pg_payment_revoke_id = models.CharField("ID транзакции отмены", max_length=200, blank=True, null=True)
    pg_payment_refund_id = models.CharField("ID транзакции возврата", max_length=200, blank=True, null=True)
    pg_revoke_status = models.CharField("Статус отмены платежа", max_length=200, blank=True, null=True)
    pg_refund_status = models.CharField("Статус возврата", max_length=200, blank=True, null=True)
    pg_reference = models.CharField("Уникальный идентификатор банковской транзакции, который назначается банком (RRN)", max_length=200, blank=True, null=True)
    pg_intreference = models.CharField("Уникальный идентификатор банковской транзакции, который назначается банком (ARN)", max_length=200, blank=True, null=True)

    pg_failure_code = models.CharField("Код ошибки возврата. Есть только у возвратов со статусом «error»", max_length=200, blank=True, null=True)
    pg_failure_description = models.CharField("Описание ошибки возврата. Есть только у возвратов со статусом «error»", max_length=200, blank=True, null=True)

    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Изменено", auto_now_add=True)

    def __str__(self):
        return f"Транзакция #{self.pk}"
    
    class Meta:
        verbose_name = "Транзакция"
        verbose_name_plural = "Транзакции"
