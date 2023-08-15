from django.contrib import admin

from .models import User, Order, Ticket, TicketAttachment, SMSMessage
# Register your models here.

admin.site.register(User)
admin.site.register(Order)
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
