import random
import string
from typing import List

from celery import shared_task, states
from celery.exceptions import Ignore
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.admin.models import ADDITION, CHANGE, LogEntry
from django.contrib.admin.options import get_content_type_for_model
from django.core import serializers
from django.core.cache import cache
from django.db import connections, ProgrammingError
from materialized_queries_manager.models import MaterializedQuery
from materialized_queries_manager.utils import refresh

logger = get_task_logger(__name__)


def _create_materialized_view(cursor, name, query):
    cursor.execute(f"CREATE MATERIALIZED VIEW {name} AS {query}")
    cursor.execute(f"GRANT SELECT ON {name} TO {settings.POSTGRES_SUPERSET_USER}")


@shared_task(bind=True)
def create_materialized_view(  # noqa
    self, user_id, old_obj, new_obj, change_message: str
):
    try:
        old_obj = next(serializers.deserialize("json", old_obj)).object
    except StopIteration:
        old_obj = None
    new_obj: MaterializedQuery = next(serializers.deserialize("json", new_obj)).object

    self.update_state(
        state=states.STARTED,
        meta=f"Processing Materialized Query {new_obj.matviewname}.",
    )

    with cache.lock("updating:materialized_view:worker:lock:" + new_obj.matviewname):
        worker_var = "updating:materialized_view:worker:" + new_obj.matviewname
        cache.get(worker_var)
        cache.set(worker_var, self.request.id)

    with cache.lock("updating:materialized_view:lock:" + new_obj.matviewname):
        if cache.get(worker_var) != self.request.id:
            self.update_state(
                state=states.IGNORED,
                meta=f"There is another worker with more recent changes for the Materialized Query {new_obj.matviewname}.",
            )
            raise Ignore()

        add = old_obj is None

        with connections["achilles"].cursor() as cursor:
            if not add:
                if (
                    old_obj.matviewname != new_obj.matviewname
                    and old_obj.definition == new_obj.definition
                ):
                    cursor.execute(
                        f"ALTER MATERIALIZED VIEW {old_obj.matviewname} RENAME TO {new_obj.matviewname}"
                    )
                elif old_obj.definition != new_obj.definition:
                    # don't drop the old view yet. rename the view to a random name
                    #  just as a backup if there is something wrong with the new
                    #  query or name
                    allowed_characters = string.ascii_letters + "_"
                    tmp_name = "".join(
                        random.choice(allowed_characters) for _ in range(30)
                    )

                    cursor.execute(
                        f"ALTER MATERIALIZED VIEW {old_obj.matviewname} RENAME TO {tmp_name}"
                    )

                    try:
                        _create_materialized_view(
                            cursor, new_obj.matviewname, new_obj.definition
                        )
                    except ProgrammingError as e:
                        self.update_state(
                            state=states.FAILURE,
                            meta=f"Error while creating the materialized view {new_obj.matviewname} in the underlying database.",
                            traceback=e,
                        )
                        cursor.execute(
                            f"ALTER MATERIALIZED VIEW {tmp_name} RENAME TO {old_obj.matviewname}"
                        )
                        raise Ignore()

                    cursor.execute(f"DROP MATERIALIZED VIEW {tmp_name}")

            else:
                try:
                    _create_materialized_view(
                        cursor, new_obj.matviewname, new_obj.definition
                    )
                except ProgrammingError as e:
                    self.update_state(
                        state=states.FAILURE,
                        meta=f"Error while creating the materialized view {new_obj.matviewname} in the underlying database.",
                        traceback=e,
                    )
                    raise Ignore()

        if add:
            self.update_state(
                state=states.SUCCESS,
                meta=f"Materialized view {new_obj.matviewname} successfully created.",
            )
            LogEntry.objects.log_action(
                user_id=user_id,
                content_type_id=get_content_type_for_model(new_obj).pk,
                object_id=new_obj.pk,
                object_repr=str(new_obj),
                action_flag=ADDITION,
                change_message=change_message,
            )
        else:
            self.update_state(
                state=states.SUCCESS,
                meta=f"Materialized view {new_obj.matviewname} successfully change.",
            )
            LogEntry.objects.log_action(
                user_id=user_id,
                content_type_id=get_content_type_for_model(new_obj).pk,
                object_id=new_obj.pk,
                object_repr=str(new_obj),
                action_flag=CHANGE,
                change_message=change_message,
            )

        raise Ignore()


@shared_task
def refresh_materialized_views_task(query_set):
    query_set = serializers.deserialize("json", query_set)
    refresh(logger, query_set=[mat_query.object for mat_query in query_set])
