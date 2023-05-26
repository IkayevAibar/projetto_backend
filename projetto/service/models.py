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

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    flat_layout = models.ForeignKey("residence.Layout", on_delete=models.CASCADE)
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
    script_name = models.CharField(max_length=200, blank=True, null=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    status = models.CharField(max_length=20)
    description = models.TextField("Описание", blank=True, null=True)

    pg_payment_id = models.CharField(max_length=200, blank=True, null=True)
    pg_3ds = models.CharField(max_length=200, blank=True, null=True)
    pg_3d_acsurl = models.CharField(max_length=200, blank=True, null=True)
    pg_3d_md = models.CharField(max_length=200, blank=True, null=True)
    pg_3d_pareq = models.CharField(max_length=200, blank=True, null=True)
    pg_recurring_profile = models.CharField(max_length=200, blank=True, null=True)
    pg_card_id = models.CharField(max_length=200, blank=True, null=True)
    pg_card_token = models.CharField(max_length=200, blank=True, null=True)
    pg_auth_code = models.CharField(max_length=200, blank=True, null=True)
    pg_salt = models.CharField(max_length=200, blank=True, null=True)
    pg_sig = models.CharField(max_length=200, blank=True, null=True)
    pg_datetime = models.CharField(max_length=200, blank=True, null=True)

    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Изменено", auto_now_add=True)

    def __str__(self):
        return f"Транзакция #{self.pk}"
    
    class Meta:
        verbose_name = "Транзакция"
        verbose_name_plural = "Транзакции"
