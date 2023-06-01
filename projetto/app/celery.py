from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

# Установите имя вашего проекта
app = Celery('app')

# Установите параметры для подключения к брокеру сообщений (например, Redis или RabbitMQ)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически обнаруживайте и регистрируйте задачи из файла tasks.py в приложениях Django
app.autodiscover_tasks()
