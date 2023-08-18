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
    slug = models.CharField(max_length=4, blank=True)
    title = models.CharField("Название ЖК", max_length=150, blank=True)
    description = models.TextField("Описание", max_length=2500, blank=True)
    exploitation_date = models.DateField("Дата эксплуатации",default=timezone.now)
    city = models.ForeignKey(City, verbose_name="Город", on_delete=models.CASCADE , default=2, blank=True)
    address = models.CharField("Адрес", max_length=150, blank=True)
    website_url = models.URLField("Сайт", max_length=150, blank=True, null=True)
    gen_plan = models.ImageField("Генеральный план", upload_to='residence/gen_plans/', blank=True, null=True)
    poster = models.ImageField("Постер", upload_to='residence/posters/', blank=True, null=True)
    class Meta:
        verbose_name = 'Жилой комплекс'
        verbose_name_plural = 'Жилые комплексы'
        ordering = ['-exploitation_date']
    
    def __str__(self):
        return f"{self.title}"
   
class Attachment(Timestamp):
    residence_id = models.ForeignKey("Residence", on_delete=models.CASCADE, blank=True)
    name = models.CharField(max_length=100, blank=True)
    image = models.ImageField("Attachment", upload_to='residence/images/', blank=True)

    class Meta:
        verbose_name = 'Вложение'
        verbose_name_plural = 'Вложении'

class Cluster(Timestamp):
    name = models.CharField("Название", max_length=50, blank=True, help_text="Пример: Пятно/Блок 1/A")
    residence_id = models.ForeignKey("Residence", related_name='clusters', on_delete=models.CASCADE, blank=True)
    max_floor = models.IntegerField("Максимальный этаж", default=0, blank=True)
    date_to_start_sell = models.DateField("Дата начала продаж", blank=True, null=True)
    class Meta:
        verbose_name = 'Пятно'
        verbose_name_plural = 'Пятны'
        ordering = ['name']
    
    def __str__(self):
        split_name = self.name.split(' ')
        if(len(split_name)>1):
            return f"{self.name} из {self.residence_id.title}"
        return f"Пятно Блок-{self.name} из {self.residence_id.title}"

class Floor(Timestamp):
    floor_numbers = models.CharField("Номера Этажей",max_length=50, blank=True, help_text="Пример: 1,2,3")
    clusters = models.ManyToManyField("Cluster", related_name='floors', blank=True)
    scheme = models.FileField("Схема", upload_to='floor/schemes/', blank=True)
    class Meta:
        verbose_name = 'Этаж'
        verbose_name_plural = 'Этажи'
    
    def __str__(self):
        return f"Этажи {self.floor_numbers}"


class Apartment(Timestamp):
    floor = models.ForeignKey("Floor", related_name='apartments', on_delete=models.CASCADE, blank=True)
    exact_floor = models.IntegerField("Точный номер этажа", blank=True)
    door_number = models.CharField("Номер квартиры",max_length=50, blank=True, help_text="132")
    room_number = models.IntegerField("Количество комнат", blank=True)
    area = models.FloatField("Плошадь(m²)", blank=True)
    layouts = models.ManyToManyField("Layout", verbose_name="Варианты планировки", related_name='apartments', blank=True)
    class Meta:
        verbose_name = 'Квартира'
        verbose_name_plural = 'Квартиры'
        
        ordering = ['id']
    
    def __str__(self):
        return f"{self.id}. Квартира №{self.door_number} из этажов {self.floor.floor_numbers}"



class Layout(Timestamp):
    TYPE_CHOICES = (
        ('def', 'Основная'),
        ('ver', 'Вертикальная'),
        ('hor', 'Горизонтальная'),
    )

    variant = models.IntegerField("Вариант", blank=True, help_text="Номер варианта которое отоборжается в планировке")
    type_of_apartment = models.CharField("Тип квартиры", choices=TYPE_CHOICES, max_length=100, blank=True)
    pdf = models.FileField("PDF", upload_to="PDF/", blank=True)
    preview = models.ImageField("Превью", upload_to="preview/", blank=True)
    before_view = models.ImageField("Вид до", upload_to="before_view/", blank=True)
    after_view = models.ImageField("Вид после", upload_to="after_view/", blank=True)
    price = models.CharField(max_length=10, blank=True)
    room_number = models.IntegerField("Количество комнат", blank=True)

    class Meta:
        verbose_name = 'Планировка'
        verbose_name_plural = 'Планировки'
        ordering = ['id']

    def __str__(self):
        return f"{self.id}. Планировка №{self.id} {self.room_number}.{self.variant}/{self.type_of_apartment}"

    def get_appartment(self, apartment_id):
        appartment = self.apartments.filter(id=apartment_id).first()
        return appartment



