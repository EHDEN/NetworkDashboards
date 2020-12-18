import random
import string
import traceback
from contextlib import closing

from celery import shared_task, states
from celery.exceptions import Ignore
from django.conf import settings
from django.contrib.admin.models import ADDITION, CHANGE, LogEntry
from django.contrib.admin.options import get_content_type_for_model
from django.core import serializers
from django.core.cache import cache
from django.db import connections, ProgrammingError
from materialized_queries_manager.models import MaterializedQuery


def _create_materialized_view(cursor, name, query):
    cursor.execute(f"CREATE MATERIALIZED VIEW {name} AS {query}")
    cursor.execute(f"GRANT SELECT ON {name} TO {settings.POSTGRES_SUPERSET_USER}")


@shared_task(bind=True)
def create_materialized_view(  # noqa
    self, user_id, old_obj: dict, new_obj, add: bool, change_message: str
):
    new_obj: MaterializedQuery = next(serializers.deserialize("json", new_obj)).object

    with cache.lock("updating:materialized_view:worker:lock:" + new_obj.name):
        worker_var = "updating:materialized_view:worker:" + new_obj.name
        cache.get(worker_var)
        cache.set(worker_var, self.request.id)

    with cache.lock("updating:materialized_view:lock:" + new_obj.name):
        if cache.get(worker_var) != self.request.id:
            return

        with closing(connections["achilles"].cursor()) as cursor:
            if new_obj.id:
                if (
                    old_obj["name"] != new_obj.name
                    and old_obj["query"] == new_obj.query
                ):
                    cursor.execute(
                        f"ALTER MATERIALIZED VIEW {old_obj['name']} RENAME TO {new_obj.name}"
                    )
                elif old_obj["query"] != new_obj.query:
                    # don't drop the old view yet. rename the view to a random name
                    #  just as a backup if there is something wrong with the new
                    #  query or name
                    allowed_characters = string.ascii_letters + string.digits + "_"
                    tmp_name = "".join(
                        random.choice(allowed_characters) for _ in range(30)
                    )

                    cursor.execute(
                        f"ALTER MATERIALIZED VIEW {old_obj['name']} RENAME TO {tmp_name}"
                    )

                    try:
                        _create_materialized_view(cursor, new_obj.name, new_obj.query)
                    except ProgrammingError as e:
                        self.update_state(
                            state=states.FAILURE,
                            meta={
                                "exc_type": type(e).__name__,
                                "exc_message": traceback.format_exc().split("\n"),
                            },
                        )
                        cursor.execute(
                            f"ALTER MATERIALIZED VIEW {tmp_name} RENAME TO {old_obj['name']}"
                        )
                        cache.unlock("updating:materialized_view:lock:" + new_obj.name)
                        raise Ignore()

                    cursor.execute(f"DROP MATERIALIZED VIEW {tmp_name}")

            else:
                try:
                    _create_materialized_view(cursor, new_obj.name, new_obj.query)
                except ProgrammingError as e:
                    self.update_state(
                        state=states.FAILURE,
                        meta={
                            "exc_type": type(e).__name__,
                            "exc_message": traceback.format_exc().split("\n"),
                        },
                    )
                    cache.unlock("updating:materialized_view:lock:" + new_obj.name)
                    raise Ignore()

        new_obj.save()
        if add:
            LogEntry.objects.log_action(
                user_id=user_id,
                content_type_id=get_content_type_for_model(new_obj).pk,
                object_id=new_obj.pk,
                object_repr=str(new_obj),
                action_flag=ADDITION,
                change_message=change_message,
            )
        else:
            LogEntry.objects.log_action(
                user_id=user_id,
                content_type_id=get_content_type_for_model(new_obj).pk,
                object_id=new_obj.pk,
                object_repr=str(new_obj),
                action_flag=CHANGE,
                change_message=change_message,
            )
