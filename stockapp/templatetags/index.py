from django import template
register = template.Library()


@register.filter
def index(indexable, i):
    return indexable[i]


@register.filter
def subtract(value, arg):
    value = int(value)
    arg = int(arg)
    return value - arg
