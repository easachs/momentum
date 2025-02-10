from django.contrib import admin
from .models import Application

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'status', 'user', 'created_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('title', 'company')
