from django.contrib import admin

from .models import User, Order, TransactionResponce, TransactionCancel, TransactionPayment, \
    TransactionRevoke, TransactionStatus, Ticket, TicketAttachment, SMSMessage
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


class SMSMessageAdmin(admin.ModelAdmin):
    list_display = ['phone', 'code', 'sms_status', 'created_at', 'updated_at']
    list_filter = ['sms_status']

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
    
admin.site.register(SMSMessage, SMSMessageAdmin)
