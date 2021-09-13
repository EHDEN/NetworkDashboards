# Copied from https://github.com/celery/django-celery/blob/a78b3a5e0d3b28ee550c70cc509d608744c88337/djcelery/contrib/test_runner.py
# This avoids having to install the package to just use this class from it

from celery import current_app
from django.conf import settings
from django.test.runner import DiscoverRunner


def _set_eager():
    settings.CELERY_ALWAYS_EAGER = True
    current_app.conf.CELERY_ALWAYS_EAGER = True
    settings.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
    current_app.conf.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True


class CeleryTestSuiteRunner(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        _set_eager()
        super().setup_test_environment(**kwargs)
