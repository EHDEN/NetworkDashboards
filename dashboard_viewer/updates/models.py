from django.db import models
from uploader.models import UploadHistory


class RequestsGroup(models.Model):
    name = models.CharField(max_length=255)
    active = models.BooleanField(
        default=True,
        help_text="Allows to deactivate this group of requests from being "
        "processed without having to delete associated records",
    )

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.name


class Request(models.Model):
    group = models.ForeignKey(
        RequestsGroup, on_delete=models.CASCADE, related_name="requests"
    )
    request_arguments_template = models.TextField(
        blank=True,
        help_text="Jinja2 template that must render valid JSON. This JSON will then be converted to "
        'a python dict which will be used to define the arguments of the <a href="https://2.'
        'python-requests.org/en/master/api/#requests.Session.request" target="_blank">Session'
        ".request</a> method. Note that both the <b>method</b> and <b>url</b> arguments are "
        "required. To build the template you have access to the uploaded records, grouped by "
        'analysis id (<b>achilles_results</b>) (ex: {1: [{"stratum_1":10, ...}, {{"stratum_1":'
        "11, ...}}], ...}), the django model object of the target Data Source (<b>data_source</b>)"
        " and the responses to the previous requests of the same group (<b>responses</b>). An"
        ' example of a valid template to send the number of patients of a datasource: {"url":'
        ' "http://server.com" , "method": "post", "data": {"patient_count": "{{ achilles_results'
        '.0.0.count_value }}"}}',
    )
    success_condition_template = models.TextField(
        blank=True,
        null=True,
        help_text="A Jinja2 template that must render a boolean expression that indicates that this "
        "request was successful and the next requests of the associated request group can "
        'be performed. On this template, you have access to the returned <a href="https://'
        'docs.python-requests.org/en/master/api/#requests.Response" target="_blank">requests'
        ".Response</a> object (<b>response</b>). Ex: {{ response.status_code }} == 200",
    )
    order = models.IntegerField()

    class Meta:
        ordering = ("order",)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"Group: {self.group} - Order: {self.order}"


class RequestsGroupLog(models.Model):
    group = models.ForeignKey(RequestsGroup, on_delete=models.CASCADE)
    trigger_upload = models.ForeignKey(UploadHistory, on_delete=models.CASCADE)
    success_count = models.IntegerField(default=0)
    time = models.DateTimeField(auto_now_add=True)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"Group: {self.group.name} - Data Source: {self.trigger_upload.data_source.acronym} - Requests Time: {self.time}"


class RequestLog(models.Model):
    group = models.ForeignKey(
        RequestsGroupLog, on_delete=models.CASCADE, related_name="requests"
    )
    request = models.ForeignKey(Request, on_delete=models.CASCADE)
    request_arguments_template_render = models.TextField(null=True)
    success_condition_template_render = models.TextField(null=True)
    success = models.BooleanField(default=True)
    exception = models.TextField(null=True)
