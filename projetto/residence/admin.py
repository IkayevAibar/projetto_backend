from django.contrib import admin
from .models import Attachment, Cluster, Floor, Layout, Residence, Apartment
# from service.models import User

# Register your models here.
admin.site.register(Attachment)
admin.site.register(Cluster)
admin.site.register(Floor)
admin.site.register(Layout)
admin.site.register(Residence)
admin.site.register(Apartment)