from celery import shared_task
from .models import Order
from app.celery import app as celery_app

@celery_app.task
def start_task(order_id):
    order = Order.objects.get(id=order_id)
    result = order.generate_doc()
    return result
