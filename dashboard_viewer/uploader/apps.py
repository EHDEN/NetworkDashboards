from django.apps import AppConfig


class UploaderConfig(AppConfig):
    name = "uploader"

    def ready(self):
        from . import signals  # noqa
