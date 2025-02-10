from django.contrib import admin
from .models import Habit

@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'category', 'frequency', 'created_at')
    list_filter = ('category', 'frequency', 'created_at')
    search_fields = ('name', 'description', 'user__email')
    ordering = ('-created_at',)
