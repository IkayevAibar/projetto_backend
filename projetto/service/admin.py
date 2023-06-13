from django.contrib import admin

from .models import User, Order, TransactionResponce, TransactionCancel, TransactionPayment, TransactionRevoke, TransactionStatus, Ticket, TicketAttachment
# Register your models here.

admin.site.register(User)
admin.site.register(Order)
admin.site.register(TransactionResponce)
admin.site.register(TransactionPayment)
admin.site.register(TransactionStatus)
admin.site.register(TransactionCancel)
admin.site.register(TransactionRevoke)
admin.site.register(Ticket)
admin.site.register(TicketAttachment)
