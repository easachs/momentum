from django import forms
from .models import Application, Contact

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['company', 'title', 'status', 'due', 'link', 'notes']
        widgets = {
            'due': forms.DateInput(attrs={
                'type': 'date',
                'class': (
                    'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                    'focus:border-blue-500 focus:ring-blue-500'
                )
            }),
            'notes': forms.Textarea(attrs={
                'class': (
                    'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                    'focus:border-blue-500 focus:ring-blue-500 h-32'
                )
            }),
            'link': forms.URLInput(attrs={
                'class': (
                    'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                    'focus:border-blue-500 focus:ring-blue-500'
                ),
                'placeholder': 'https://'
            }),
            'status': forms.Select(attrs={
                'class': (
                    'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                    'focus:border-blue-500 focus:ring-blue-500'
                )
            }),
            'company': forms.TextInput(attrs={
                'class': (
                    'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                    'focus:border-blue-500 focus:ring-blue-500'
                )
            }),
            'title': forms.TextInput(attrs={
                'class': (
                    'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                    'focus:border-blue-500 focus:ring-blue-500'
                )
            }),
        }
        help_texts = {
            'due': 'When is this application due?',
            'notes': 'Add any additional details about this application (optional)',
            'link': 'Add a link to the application (optional)',
            'status': 'What is the status of this application?',
            'company': 'What company is this application for?',
            'title': 'What is the title of this application?',
        }

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'role', 'company', 'email', 'phone', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': (
                    'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                    'focus:border-blue-500 focus:ring-blue-500 h-32'
                ),
                'rows': 3
            }),
            'phone': forms.TextInput(attrs={
                'class': (
                    'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                    'focus:border-blue-500 focus:ring-blue-500'
                ),
                'type': 'tel',
                'pattern': '[0-9]{3}-[0-9]{3}-[0-9]{4}',
                'placeholder': '123-456-7890'
            }),
            'email': forms.EmailInput(attrs={
                'class': (
                    'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                    'focus:border-blue-500 focus:ring-blue-500'
                ),
                'placeholder': 'email@example.com'
            }),
            'role': forms.Select(attrs={
                'class': (
                    'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                    'focus:border-blue-500 focus:ring-blue-500'
                )
            }),
            'company': forms.TextInput(attrs={
                'class': (
                    'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                    'focus:border-blue-500 focus:ring-blue-500'
                )
            }),
            'name': forms.TextInput(attrs={
                'class': (
                    'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                    'focus:border-blue-500 focus:ring-blue-500'
                )
            }),
        }
        help_texts = {
            'name': 'Full name of the contact',
            'role': 'Their role in the hiring process',
            'company': 'Company they work for (optional)',
            'email': 'Email address for the contact (optional)',
            'phone': 'Phone number in format: 123-456-7890 (optional)',
            'notes': 'Any additional information about this contact (optional)'
        }
