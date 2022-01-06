import constance
from django.http import (
    HttpResponse,
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


def production_media_files(request, path):
    response = HttpResponse()
    del response["Content-Type"]

    if not path.startswith("achilles_results_files"):
        response["X-Accel-Redirect"] = f"/normal_media/{path}"
    else:
        if not request.user.is_staff:
            return HttpResponseForbidden()

        if len(path[23:].split("/")) != 3:  # only allow serving files, not directories
            return HttpResponseForbidden()

        response["X-Accel-Redirect"] = f"/{path}"

    return response
