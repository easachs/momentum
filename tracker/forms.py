from django import forms
from .models import Habit

class HabitForm(forms.ModelForm):
    class Meta:
        model = Habit
        fields = ['name', 'category', 'frequency', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md',
                'placeholder': 'Exercise, Read, Meditate...'
            }),
            'category': forms.Select(attrs={
                'class': 'shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md'
            }),
            'frequency': forms.Select(attrs={
                'class': 'shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md'
            }),
            'description': forms.Textarea(attrs={
                'class': 'shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md',
                'rows': 3,
                'placeholder': 'Optional description of your habit...'
            })
        }
        help_texts = {
            'name': 'Give your habit a clear, actionable name',
            'category': 'Choose a category to help organize your habits',
            'frequency': 'How often do you want to do this habit?',
            'description': 'Add any additional details about your habit (optional)'
        } 