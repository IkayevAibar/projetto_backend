from django.db import models
from django.utils import timezone


class Timestamp(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    class Meta:
        abstract = True

class City(Timestamp):
    initials = models.CharField(max_length=3)
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'
    
    def __str__(self):
        return f"{self.initials} {self.name}"

class Residence(Timestamp):
    title = models.CharField(max_length=150)
    description = models.TextField(max_length=2500)
    exploitation_date = models.DateField(default=timezone.now)
    city = models.ForeignKey(City, on_delete=models.CASCADE , default=2)
    class Meta:
        verbose_name = 'Жилой комплекс'
        verbose_name_plural = 'Жилые комплексы'
        ordering = ['-exploitation_date']
    
    def __str__(self):
        return f"{self.title}"
    
class Attachment(Timestamp):
    residence_id = models.ForeignKey("Residence", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    image = models.ImageField("Attachment", upload_to='attachments/')

    class Meta:
        verbose_name = 'Вложение'
        verbose_name_plural = 'Вложении'

class Cluster(Timestamp):
    name = models.CharField(max_length=50)
    residence_id = models.ForeignKey("Residence", related_name='clusters', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Пятно'
        verbose_name_plural = 'Пятны'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} из {self.residence_id.title}"


class Floor(Timestamp):
    number = models.IntegerField()
    cluster = models.ForeignKey(Cluster, related_name='floors', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Этаж'
        verbose_name_plural = 'Этажи'
        ordering = ['number']


class Apartment(Timestamp):
    room_number = models.IntegerField()
    area = models.FloatField()
    floor = models.ForeignKey(Floor, related_name='apartments', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Квартира'
        verbose_name_plural = 'Квартиры'
        ordering = ['id']


class Layout(Timestamp):
    name = models.CharField(max_length=150)
    pdf = models.FileField("PDF", upload_to="PDF/")
    apartment = models.ForeignKey(Apartment, related_name='layouts', on_delete=models.CASCADE)
    price = models.CharField(max_length=10)
    description = models.TextField(max_length=2500)


    class Meta:
        verbose_name = 'Планировка'
        verbose_name_plural = 'Планировки'
        ordering = ['id']


class Ticket(Timestamp):
    full_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    email = models.CharField(max_length=30)
    description = models.TextField(max_length=1000, null=True, blank=True)

    class Meta:
        verbose_name = 'Тикет'
        verbose_name_plural = 'Тикеты'
        ordering = ['created_at']

class TicketAttachment(Timestamp):
    ticket = models.ForeignKey("Ticket", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    file = models.FileField("Screenshot", upload_to='tickets/')


    class Meta:
        verbose_name = 'Вложение для Тикета'
        verbose_name_plural = 'Вложении  для Тикета'
