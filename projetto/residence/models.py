from django.db import models
from django.utils import timezone


class Timestamp(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class City(Timestamp):
    initials = models.CharField(max_length=3, blank=True)
    name = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'
    
    def __str__(self):
        return f"{self.initials} {self.name}"

class Residence(Timestamp):
    title = models.CharField(max_length=150, blank=True)
    description = models.TextField(max_length=2500, blank=True)
    exploitation_date = models.DateField(default=timezone.now)
    city = models.ForeignKey(City, on_delete=models.CASCADE , default=2, blank=True)
    class Meta:
        verbose_name = 'Жилой комплекс'
        verbose_name_plural = 'Жилые комплексы'
        ordering = ['-exploitation_date']
    
    def __str__(self):
        return f"{self.title}"
    
class Attachment(Timestamp):
    residence_id = models.ForeignKey("Residence", on_delete=models.CASCADE, blank=True)
    name = models.CharField(max_length=100, blank=True)
    image = models.ImageField("Attachment", upload_to='attachments/', blank=True)

    class Meta:
        verbose_name = 'Вложение'
        verbose_name_plural = 'Вложении'

class Cluster(Timestamp):
    name = models.CharField(max_length=50, blank=True)
    residence_id = models.ForeignKey("Residence", related_name='clusters', on_delete=models.CASCADE, blank=True)

    class Meta:
        verbose_name = 'Пятно'
        verbose_name_plural = 'Пятны'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} из {self.residence_id.title}"


class Floor(Timestamp):
    number = models.IntegerField("Номер Этажа", blank=True)
    cluster = models.ForeignKey(Cluster, related_name='floors', on_delete=models.CASCADE, blank=True)

    class Meta:
        verbose_name = 'Этаж'
        verbose_name_plural = 'Этажи'
        ordering = ['number']


class Apartment(Timestamp):
    room_number = models.IntegerField("Номер квартиры", blank=True)
    area = models.FloatField("Размер квартиры", blank=True)
    floor = models.ForeignKey(Floor, related_name='apartments', on_delete=models.CASCADE, blank=True)

    class Meta:
        verbose_name = 'Квартира'
        verbose_name_plural = 'Квартиры'
        ordering = ['id']


class Layout(Timestamp):
    name = models.CharField(max_length=150, blank=True)
    pdf = models.FileField("PDF", upload_to="PDF/", blank=True)
    apartment = models.ForeignKey(Apartment, related_name='layouts', on_delete=models.CASCADE, blank=True)
    price = models.CharField(max_length=10, blank=True)
    description = models.TextField(max_length=2500, blank=True)


    class Meta:
        verbose_name = 'Планировка'
        verbose_name_plural = 'Планировки'
        ordering = ['id']


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

