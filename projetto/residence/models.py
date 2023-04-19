from django.db import models
from django.utils import timezone



class Residence(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField(max_length=2500)
    exploitation_date = models.DateField(default=timezone.now)
    
    class Meta:
        verbose_name = 'Жилой комплекс'
        verbose_name_plural = 'Жилые комплексы'
        ordering = ['-exploitation_date']
    
    def __str__(self):
        return f"{self.title}"
    
class Attachment(models.Model):
    residence_id = models.ForeignKey("Residence", on_delete=models.CASCADE)
    image = models.ImageField("Attachment", upload_to='attachments/')

    class Meta:
        verbose_name = 'Вложение'
        verbose_name_plural = 'Вложения'

class Cluster(models.Model):
    name = models.CharField(max_length=50)
    residence_id = models.ForeignKey("Residence", related_name='clusters', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Пятно'
        verbose_name_plural = 'Пятны'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} из {self.residence_id.title}"

# class Block(models.Model):
#     name = models.CharField(max_length=150)
#     address = models.CharField(max_length=250)
#     cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE)

#     class Meta:
#         verbose_name = 'Блок'
#         verbose_name_plural = 'Блоки'
#         ordering = ['name']


class Floor(models.Model):
    number = models.IntegerField()
    cluster = models.ForeignKey(Cluster, related_name='floors', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Этаж'
        verbose_name_plural = 'Этажи'
        ordering = ['number']


class Apartment(models.Model):
    number = models.IntegerField()
    area = models.FloatField()
    floor = models.ForeignKey(Floor, related_name='apartments', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Квартира'
        verbose_name_plural = 'Квартиры'
        ordering = ['number']


class Layout(models.Model):
    name = models.CharField(max_length=150)
    pdf = models.FileField("PDF", upload_to="PDF/")
    apartment = models.ForeignKey(Apartment, related_name='layouts', on_delete=models.CASCADE)
    price = models.CharField(max_length=10)

    class Meta:
        verbose_name = 'Планировка'
        verbose_name_plural = 'Планировки'
        ordering = ['name']


