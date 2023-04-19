from django.contrib import admin
from .models import Attachment, Cluster, Floor, Layout, Residence, Apartment
from service.models import User

# Register your models here.
admin.site.register(User)