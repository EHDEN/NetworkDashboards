from django import template
from pydoc import locate

register = template.Library()


@register.filter
def isinst(val, class_str):
    return isinstance(val, locate(class_str))
