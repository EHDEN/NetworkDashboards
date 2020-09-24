from django import template

register = template.Library()


@register.filter
def isinst(val, class_str):
    return isinstance(val, class_str)
