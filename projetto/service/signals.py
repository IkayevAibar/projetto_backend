from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import User

@receiver(pre_save, sender=User)
def update_user_updated_at(sender, instance, **kwargs):
    instance.updated_at = timezone.now()