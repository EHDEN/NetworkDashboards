from functools import wraps

from django.conf import settings
from django.http import HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt


def uploader_decorator(view_func):
    """
    If in single application mode
      check if the request is being sent from the main application.
      If not response with 403
    Else don't do any verification
    """
    wrapped_view = csrf_exempt(view_func)
    if not settings.SINGLE_APPLICATION_MODE:

        def check_host(request, *args, **kwargs):
            if request.get_host() != settings.MAIN_APPLICATION_HOST:
                return HttpResponseForbidden()
            return view_func(request, *args, **kwargs)

        return wraps(wrapped_view)(check_host)

    return view_func
