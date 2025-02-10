from django import forms
from .models import Book

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            'title', 'author', 'pages', 'genre', 
            'date_started', 'date_finished', 'status', 'rating'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': (
                    'shadow appearance-none border rounded w-full py-2 px-3 '
                    'text-gray-700 leading-tight focus:outline-none '
                    'focus:shadow-outline'
                ),
                'placeholder': 'Book title'
            }),
            'author': forms.TextInput(attrs={
                'class': (
                    'shadow appearance-none border rounded w-full py-2 px-3 '
                    'text-gray-700 leading-tight focus:outline-none '
                    'focus:shadow-outline'
                ),
                'placeholder': 'Author name'
            }),
            'pages': forms.NumberInput(attrs={
                'class': (
                    'shadow appearance-none border rounded w-full py-2 px-3 '
                    'text-gray-700 leading-tight focus:outline-none '
                    'focus:shadow-outline'
                ),
                'placeholder': 'Number of pages'
            }),
            'date_started': forms.DateInput(attrs={
                'type': 'date',
                'class': (
                    'shadow appearance-none border rounded w-full py-2 px-3 '
                    'text-gray-700 leading-tight focus:outline-none '
                    'focus:shadow-outline'
                ),
            }),
            'date_finished': forms.DateInput(attrs={
                'type': 'date',
                'class': (
                    'shadow appearance-none border rounded w-full py-2 px-3 '
                    'text-gray-700 leading-tight focus:outline-none '
                    'focus:shadow-outline'
                ),
            }),
            'status': forms.Select(attrs={
                'class': (
                    'shadow appearance-none border rounded w-full py-2 px-3 '
                    'text-gray-700 leading-tight focus:outline-none '
                    'focus:shadow-outline'
                ),
            }),
            'genre': forms.Select(attrs={
                'class': (
                    'shadow appearance-none border rounded w-full py-2 px-3 '
                    'text-gray-700 leading-tight focus:outline-none '
                    'focus:shadow-outline'
                ),
            }),
            'rating': forms.NumberInput(attrs={
                'class': (
                    'shadow appearance-none border rounded w-full py-2 px-3 '
                    'text-gray-700 leading-tight focus:outline-none '
                    'focus:shadow-outline'
                ),
                'placeholder': 'Rating (1-5)',
                'min': '1',
                'max': '5'
            })
        }
