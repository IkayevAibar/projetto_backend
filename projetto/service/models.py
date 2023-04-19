from django.db import models
from django.contrib.auth.models import AbstractUser,UserManager as BaseUserAdmin
from .managers import UserManager

# Create your models here.
class User(AbstractUser):
    email = None 
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return "%d.%s" % (self.id, self.username)
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
