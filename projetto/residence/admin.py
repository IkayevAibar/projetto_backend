from django.contrib import admin
from django.urls import reverse, path
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.contrib.admin.widgets import ForeignKeyRawIdWidget, FilteredSelectMultiple

from .models import Attachment, Cluster, Floor, Layout, Residence, Apartment, City
from .serializers import ResidenceSerializer, ClusterSerializer
from .views import ResidenceViewSet
# from service.models import User

from django import forms

class LayoutApartmentForm(forms.ModelForm):
    apartments = forms.ModelMultipleChoiceField(
        queryset=Apartment.objects.all(),
        widget=FilteredSelectMultiple("Apartments", is_stacked=False),
        required=False,
    )

    class Meta:
        model = Layout
        fields = ['apartments', 'variant', 'type_of_apartment', 'pdf', 'price', 'room_number']
    
    # def __init__(self, *args, **kwargs):
    #     super(LayoutApartmentForm, self).__init__(*args, **kwargs)
    #     if self.instance.pk:
    #         self.fields['apartments'].initial = self.instance.apartments.all()

    def __init__(self, *args, **kwargs):
        super(LayoutApartmentForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['apartments'].initial = self.instance.apartments.all()
    
    def save(self, commit=True):
        layout = super().save(commit)
        if commit:
            selected_apartments = self.cleaned_data['apartments']
            layout.apartments.set(selected_apartments)
        return layout


# Register your models here.
class LayoutInline(admin.TabularInline):
    model = Apartment.layouts.through
    extra = 0
    verbose_name = "Вариант планировки"
    verbose_name_plural = "Варианты планировки"

class ApartmentInline(admin.TabularInline):
    model = Apartment
    extra = 0
    show_change_link = True
    fields = ('link','floor', 'door_number', 'exact_floor', 'room_number', 'area', 'layouts', 'created_at', 'updated_at')
    readonly_fields = ('link', 'created_at', 'updated_at')
    
    def link(self, obj):
        return format_html('<a href="{}">ID:{}</a>', reverse('admin:residence_apartment_change', args=[obj.id]), obj.id)
    link.short_description = 'ID'

class ClusterInline(admin.TabularInline):
    model = Cluster
    extra = 0
    fields = ('link','name', 'residence_id', 'max_floor', 'date_to_start_sell')
    readonly_fields = ('link',)
    
    def link(self, obj):
        return format_html('<a href="{}">ID:{}</a>', reverse('admin:residence_cluster_change', args=[obj.id]), obj.id)
    link.short_description = 'ID'

class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0

class FloorInline(admin.TabularInline):
    model = Floor
    extra = 0
    fields = ('link','floor_numbers', 'cluster', 'scheme', 'created_at', 'updated_at')
    readonly_fields = ('link', 'created_at', 'updated_at')
    
    def link(self, obj):
        return format_html('<a href="{}">ID:{}</a>', reverse('admin:residence_floor_change', args=[obj.id]), obj.id)
    link.short_description = 'ID'

#--------------------------------------------------------------------------------------------------------------
class CityAdmin(admin.ModelAdmin):
    list_display = ('initials', 'name', 'created_at', 'updated_at')
    search_fields = ('initials', 'name')

class ResidenceAdmin(admin.ModelAdmin):
    list_display = ('title', 'city', 'address', 'exploitation_date', 'created_at', 'updated_at')
    search_fields = ('title', 'city', 'address')
    autocomplete_fields = ['city']
    inlines = [ClusterInline, AttachmentInline]

class ClusterAdmin(admin.ModelAdmin):
    list_display = ('name', 'residence_id', 'max_floor', 'date_to_start_sell', 'created_at', 'updated_at')
    search_fields = ('name', 'residence_id')
    autocomplete_fields = ['residence_id']
    inlines = [FloorInline]

class FloorAdmin(admin.ModelAdmin):
    
    list_display = ('floor_numbers', 'cluster', 'created_at', 'updated_at')
    search_fields = ('floor_numbers', 'cluster')
    autocomplete_fields = ['cluster']
    inlines = [ApartmentInline]

class LayoutAdmin(admin.ModelAdmin):
    list_display = ('variant', 'type_of_apartment', 'price', 'room_number', 'created_at', 'updated_at')
    search_fields = ('name', 'variant', 'type_of_apartment')

    form = LayoutApartmentForm

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.apartments.set(form.cleaned_data['apartments'])

    def change_view(self, request, object_id, form_url='', extra_context=None):
        layout = self.get_object(request, object_id)
        extra_context = extra_context or {}
        extra_context['apartments'] = Apartment.objects.all()
        extra_context['selected_apartment_ids'] = layout.apartments.values_list('id', flat=True)
        
        return super().change_view(request, object_id, form_url, extra_context=extra_context)


class ApartmentAdmin(admin.ModelAdmin):
    list_display = ('door_number', 'room_number', 'floor', 'exact_floor', 'created_at', 'updated_at')
    search_fields = ('door_number', 'room_number', 'floor', 'exact_floor')
    raw_id_fields = ['floor']
    filter_horizontal = ['layouts']
    inlines = [LayoutInline]

class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'residence_id', 'created_at', 'updated_at')
    search_fields = ('name', 'residence_id')

admin.site.register(City, CityAdmin)
admin.site.register(Attachment, AttachmentAdmin)
admin.site.register(Cluster, ClusterAdmin)
admin.site.register(Floor, FloorAdmin)
admin.site.register(Layout, LayoutAdmin)
admin.site.register(Residence, ResidenceAdmin)
admin.site.register(Apartment, ApartmentAdmin)
