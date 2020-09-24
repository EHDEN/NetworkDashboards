from pydoc import locate

from django import template

register = template.Library()


@register.filter
def isinst(val, class_str):
    return type(val) is locate(class_str)
