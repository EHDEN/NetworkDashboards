
from django.db import models


class Tab(models.Model):
    title    = models.TextField()
    icon     = models.TextField()
    url      = models.URLField()
    position = models.PositiveIntegerField()
    visible  = models.BooleanField()

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"{self.title}, position: {self.position}, visible: {self.visible}"
