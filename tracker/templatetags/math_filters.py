from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """
    Multiplies the value by the argument
    Similar to Rails: helper_method :multiply
    """
    return float(value) * float(arg)

@register.filter
def divide(value, arg):
    """
    Divides the value by the argument
    Similar to Rails: helper_method :divide
    """
    if float(arg) == 0:
        return 0
    return float(value) / float(arg) 