
from django.db import models


class Tab(models.Model):
    title        = models.CharField(
        max_length=30,
        help_text="Text to appear on the tab under the icon"
    )
    icon         = models.CharField(
        max_length=20,
        help_text="Font awesome icon v4. Just the end part, e.g. fa-clock-o -> clock-o"
    )
    url          = models.URLField()
    position     = models.PositiveIntegerField()
    visible      = models.BooleanField(
        help_text="If the tab should be displayed"
    )

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"{self.title}, position: {self.position}, visible: {self.visible}"
