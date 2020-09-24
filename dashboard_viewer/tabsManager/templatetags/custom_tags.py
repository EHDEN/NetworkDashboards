from django import template
from pydoc import locate

register = template.Library()


@register.filter
def isinst(val, class_str):
    return type(val) is locate(class_str)
