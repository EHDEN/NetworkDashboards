import json
import traceback

import pandas
import requests
from celery import shared_task
from jinja2 import Template
from uploader.models import DataSource, UploadHistory

from .models import RequestLog, RequestsGroup, RequestsGroupLog


@shared_task
def send_updates(db_id: int, upload_history_id: int, achilles_results: str):
    data_source = DataSource.objects.get(id=db_id)

    responses = []
    context = {
        "achilles_results": {
            analysis_id: rows[rows.columns[1:]].to_dict("records")
            for analysis_id, rows in pandas.read_json(achilles_results).groupby(
                "analysis_id"
            )
        },
        "data_source": data_source,
        "responses": responses,
    }

    trigger_upload = UploadHistory.objects.get(id=upload_history_id)

    for group in RequestsGroup.objects.filter(active=True):
        group_log = RequestsGroupLog.objects.create(
            group=group, trigger_upload=trigger_upload
        )

        responses.clear()

        with requests.Session() as session:
            for request in group.requests.all():
                request_log = RequestLog(group=group_log, request=request)

                try:
                    template = Template(request.request_arguments_template)  # noqa

                    render_result = template.render(**context)  # noqa
                    request_log.request_arguments_template_render = render_result

                    response = session.request(**json.loads(render_result))

                    if request.success_condition_template is not None:
                        template = Template(request.success_condition_template)  # noqa
                        render_result = template.render(response=response)  # noqa

                        request_log.success_condition_template_render = render_result

                        if not bool(
                            eval(  # noqa - we trust the admins
                                request_log.success_condition_template_render
                            )
                        ):
                            raise AssertionError("Success condition not met")

                    group_log.success_count += 1
                except:  # noqa - we are logging them
                    group_log.success = False

                    request_log.success = False
                    request_log.exception = traceback.format_exc()

                    break
                finally:
                    request_log.save()

                responses.append(response)

        group_log.save()
