from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    return float(value) * float(arg)

@register.filter
def divide(value, arg):
    if float(arg) == 0:
        return 0
    return float(value) / float(arg) 