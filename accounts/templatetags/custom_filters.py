from django import template

register = template.Library()

@register.filter(name='split')
def split(value, arg):
    """Split a string into a list by delimiter"""
    if value:
        return value.split(arg)
    return []
