import constance
from django.http import (
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseServerError,
)
from django.template import loader


def server_error(_request):
    template = loader.get_template("500.html")
    context = {
        "constance_config": constance.config,
    }
    return HttpResponseServerError(template.render(context))


def not_found(request, exception):  # noqa
    template = loader.get_template("404.html")
    context = {
        "constance_config": constance.config,
    }
    return HttpResponseNotFound(template.render(context))


def forbidden(request, exception):  # noqa
    template = loader.get_template("403.html")
    context = {
        "constance_config": constance.config,
    }
    return HttpResponseForbidden(template.render(context))


def bad_request(request, exception):  # noqa
    template = loader.get_template("400.html")
    context = {
        "constance_config": constance.config,
    }
    return HttpResponseBadRequest(template.render(context))
