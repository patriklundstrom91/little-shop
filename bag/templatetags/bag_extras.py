from django import template

register = template.Library()


@register.filter
def mul(value, arg):
    """
    Multiplies value * arg in a Django template
    Usage: {{ price|mul:quantity }}
    """
    try:
        return float(value) * int(arg)
    except (ValueError, TypeError):
        return ''
