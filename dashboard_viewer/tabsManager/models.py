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
