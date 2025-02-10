from django import forms
from .models import Food, Weight

class FoodForm(forms.ModelForm):
    class Meta:
        model = Food
        fields = ['date', 'name', 'calories', 'protein', 'carbs']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': (
                    'shadow appearance-none border rounded w-full py-2 px-3 '
                    'text-gray-700 leading-tight focus:outline-none '
                    'focus:shadow-outline'
                ),
            }),
            'name': forms.TextInput(attrs={
                'class': (
                    'shadow appearance-none border rounded w-full py-2 px-3 '
                    'text-gray-700 leading-tight focus:outline-none '
                    'focus:shadow-outline'
                ),
                'placeholder': 'Food name'
            }),
            'calories': forms.NumberInput(attrs={
                'class': (
                    'shadow appearance-none border rounded w-full py-2 px-3 '
                    'text-gray-700 leading-tight focus:outline-none '
                    'focus:shadow-outline'
                ),
                'placeholder': 'Calories'
            }),
            'protein': forms.NumberInput(attrs={
                'class': (
                    'shadow appearance-none border rounded w-full py-2 px-3 '
                    'text-gray-700 leading-tight focus:outline-none '
                    'focus:shadow-outline'
                ),
                'placeholder': 'Protein (g)'
            }),
            'carbs': forms.NumberInput(attrs={
                'class': (
                    'shadow appearance-none border rounded w-full py-2 px-3 '
                    'text-gray-700 leading-tight focus:outline-none '
                    'focus:shadow-outline'
                ),
                'placeholder': 'Carbs (g)'
            })
        }

class WeightForm(forms.ModelForm):
    class Meta:
        model = Weight
        fields = ['date', 'weight']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': (
                    'shadow appearance-none border rounded w-full py-2 px-3 '
                    'text-gray-700 leading-tight focus:outline-none '
                    'focus:shadow-outline'
                ),
            }),
            'weight': forms.NumberInput(attrs={
                'class': (
                    'shadow appearance-none border rounded w-full py-2 px-3 '
                    'text-gray-700 leading-tight focus:outline-none '
                    'focus:shadow-outline'
                ),
                'placeholder': 'Weight (lbs)'
            })
        } 