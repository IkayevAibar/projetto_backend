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
    doc = models.models.FileField("Договор", upload_to='doc/')
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='created')
    price = models.IntegerField("Цена", default=0)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Изменено", auto_now_add=True)

    def __str__(self):
        return f"Заказ #{self.pk}"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

class Transaction(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    status = models.CharField(max_length=20)
    transaction_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Изменено", auto_now_add=True)

    def __str__(self):
        return f"Транзакция #{self.pk}"
    
    class Meta:
        verbose_name = "Транзакция"
        verbose_name_plural = "Транзакции"
