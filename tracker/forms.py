from django import forms
from .models import Habit

class HabitForm(forms.ModelForm):
    class Meta:
        model = Habit
        fields = ['name', 'category', 'frequency', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': (
                    'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                    'focus:border-blue-500 focus:ring-blue-500'
                ),
                'placeholder': 'Exercise, Read, Meditate...'
            }),
            'category': forms.Select(attrs={
                'class': (
                    'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                    'focus:border-blue-500 focus:ring-blue-500'
                )
            }),
            'frequency': forms.Select(attrs={
                'class': (
                    'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                    'focus:border-blue-500 focus:ring-blue-500'
                )
            }),
            'description': forms.Textarea(attrs={
                'class': (
                    'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                    'focus:border-blue-500 focus:ring-blue-500 h-32'
                ),
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
