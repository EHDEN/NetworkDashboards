
from django.conf import settings
from django.utils.html import mark_safe

from constance import config
from markdown import markdown as markdownify


class ConstanceProxy:
    """
    This class was created because the tag from django-markdownify
     wasn't rending the landing page description correctly
    """
    def __init__(self):
        for name, (_, _, type) in settings.CONSTANCE_CONFIG.items():
            if type == "markdown":
                setattr(self, name, mark_safe(markdownify(getattr(config, name))))
            else:
                setattr(self, name, getattr(config, name))
