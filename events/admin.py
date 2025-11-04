from django.db import models
from django.contrib import admin
from .models import Event


# Register your models here.
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'venue', 'city', 'country','latitude', 'longitude', 'start_date')
    list_filter = ('city', 'start_date')
    search_fields = ('name', 'city', 'venue')
    ordering = ('start_date',)
   
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'venue', 'city', 'country')
        }),
        ('Geographic Data', {
            'fields': ('latitude', 'longitude')
        }),
        ('Additional Details', {
            'fields': ('url', 'start_date'),
            'classes': ('collapse',)
        }),
    )