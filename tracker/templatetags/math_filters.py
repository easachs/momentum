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
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def percentage(value, total):
    try:
        if float(total) == 0:
            return 0
        return (float(value) / float(total)) * 100
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def filter_by_category(habits, category):
    # Handle both QuerySet and list inputs
    if hasattr(habits, 'filter'):
        return habits.filter(category=category)
    return [habit for habit in habits if getattr(habit, 'category', '') == category] 