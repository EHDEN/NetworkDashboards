from pydoc import locate

from django import template

register = template.Library()


@register.filter
def isinst(val, class_str):
    return isinstance(val, locate(class_str))
