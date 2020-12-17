import random
import string

from celery import shared_task, current_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.admin.options import get_content_type_for_model
from django.core.cache import cache
from django.db import ProgrammingError

from materialized_queries_manager.models import MaterializedQuery

logger = get_task_logger(__name__)


def _create_materialized_view(self, cursor):
    try:
        cursor.execute(f"CREATE MATERIALIZED VIEW {self.name} AS {self.query}")
    except ProgrammingError as e:
        raise ValidationError("Invalid query. " + str(e))

    cursor.execute(
        f"GRANT SELECT ON {self.name} TO {settings.POSTGRES_SUPERSET_USER}"
    )


@shared_task
def create_materialized_view(request, old_obj: MaterializedQuery, new_obj: MaterializedQuery, add: bool, change_message: str):

    if new_obj.id:
        with cache.lock("updating:materialized_view:lock:" + old_obj.name):
            worker_var = "updating:materialized_view:worker:" + old_obj.name
            cache.get(worker_var)
            cache.set(worker_var, current_task.request.id)

        if old_obj.name != new_obj.name and old_obj.query == new_obj.query:
            cursor.execute(
                f"ALTER MATERIALIZED VIEW {old_obj.name} RENAME TO {new_obj.name}"
            )
        elif old_obj.query != new_obj.query:
            # don't drop the old view yet. rename the view to a random name
            #  just as a backup if there is something wrong with the new
            #  query or name
            allowed_characters = string.ascii_letters + string.digits + "_"
            tmp_name = "".join(
                random.choice(allowed_characters) for _ in range(30)
            )

            cursor.execute(
                f"ALTER MATERIALIZED VIEW {old_obj.name} RENAME TO {tmp_name}"
            )

            try:
                _create_materialized_view(cursor)
            except ValidationError as e:
                cursor.execute(
                    f"ALTER MATERIALIZED VIEW {tmp_name} RENAME TO {old_obj.name}"
                )
                raise e

            cursor.execute(f"DROP MATERIALIZED VIEW {tmp_name}")

    else:
        _create_materialized_view(cursor)

    new_obj.save()
    if add:
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=get_content_type_for_model(new_obj).pk,
            object_id=new_obj.pk,
            object_repr=str(new_obj),
            action_flag=ADDITION,
            change_message=change_message,
        )
    else:
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=get_content_type_for_model(new_obj).pk,
            object_id=new_obj.pk,
            object_repr=str(new_obj),
            action_flag=CHANGE,
            change_message=change_message,
        )
