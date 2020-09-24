import os

from django.conf import settings
from django.core.cache import cache
from django.db import models
from model_utils.managers import InheritanceManager


class Button(models.Model):
    """
    Base class for button on the left bar
    """

    objects = InheritanceManager()

    title = models.CharField(
        max_length=30,
        help_text="Text to appear on the tab under the icon",
        unique=True,
    )
    icon = models.CharField(
        max_length=20,
        help_text="Font awesome icon v5. Just the end part, e.g. fa-clock-o -> clock-o",
    )
    position = models.IntegerField()
    visible = models.BooleanField(
        help_text="If the tab should be displayed",
    )

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"{self.title}, position: {self.position}, visible: {self.visible}"


class TabGroup(Button):
    """
    Type of buttons that can hold a submenu
    Dont't display iframes
    """


class Tab(Button):
    """
    Type of buttons that display a iframe
    Can be within a group, forming a submenu
    """

    url = models.URLField()
    group = models.ForeignKey(
        TabGroup, on_delete=models.SET_NULL, null=True, blank=True
    )


class Logo(models.Model):
    MEDIA_DIR = "logo"

    image = models.ImageField(blank=True, null=True, upload_to=MEDIA_DIR)
    url = models.URLField(blank=True, null=True)
    image_container_css = models.TextField(
        blank=True,
        default="padding: 5px 5px 5px 5px;\n" "height: 100px;\n" "margin-bottom: 10px;",
    )
    image_css = models.TextField(
        blank=True,
        default="background: #fff;\n"
        "object-fit: contain;\n"
        "width: 90px;\n"
        "height: 100%;\n"
        "border-radius: 30px;\n"
        "padding: 0 5px 0 5px;\n"
        "transition: width 400ms, height 400ms;\n"
        "position: relative;\n"
        "z-index: 5;\n",
    )
    image_on_hover_css = models.TextField(
        blank=True,
        default="max-width: none !important;\n"
        "width: 300px !important;\n"
        "height: 150px !important;",
    )

    def delete(self, using=None, keep_parents=False):
        try:
            os.remove(f"{settings.MEDIA_ROOT}/{Logo.objects.get(pk=1).image}")
        except self.DoesNotExist:
            pass

        cache.delete(self.__class__.__name__)

        super(Logo, self).delete(using, keep_parents)

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):

        try:
            os.remove(f"{settings.MEDIA_ROOT}/{Logo.objects.get(pk=1).image}")
        except Logo.DoesNotExist:
            pass
        self.pk = 1
        obj = super(Logo, self).save(force_insert, force_update, using, update_fields)
        cache.set(self.__class__.__name__, obj)

    @classmethod
    def load(cls):
        cached = cache.get(cls.__name__)
        if not cached:
            try:
                cached = Logo.objects.get(pk=1)
                cache.set(cls.__name__, cached)
            except Logo.DoesNotExist:
                pass
        return cached
