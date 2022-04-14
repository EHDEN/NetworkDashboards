import random
import string

from celery import shared_task, states
from celery.exceptions import Ignore
from celery.utils.log import get_task_logger
from django.contrib.admin.models import ADDITION, CHANGE, LogEntry
from django.contrib.admin.options import get_content_type_for_model
from django.core import serializers
from django.core.cache import cache
from django.db import connections, ProgrammingError, router, transaction

from materialized_queries_manager.models import MaterializedQuery
from materialized_queries_manager.utils import refresh

logger = get_task_logger(__name__)


@shared_task(bind=True)
def create_materialized_view(  # noqa
    self, user_id, old_obj, new_obj, change_message: str
):
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

        with transaction.atomic(
            using=router.db_for_write(MaterializedQuery)
        ), connections["achilles"].cursor() as cursor:
            if not add:
                if (
                    old_obj["matviewname"] != new_obj.matviewname
                    and old_obj["definition"] == new_obj.definition
                ):
                    cursor.execute(
                        f"ALTER MATERIALIZED VIEW {old_obj['matviewname']} RENAME TO {new_obj.matviewname}"
                    )
                elif old_obj["definition"] != new_obj.definition:
                    # don't drop the old view yet. rename the view to a random name
                    #  just as a backup if there is something wrong with the new
                    #  query or name
                    allowed_characters = string.ascii_letters + "_"
                    tmp_name = "".join(
                        random.choice(allowed_characters) for _ in range(30)
                    )

                    cursor.execute(
                        f"ALTER MATERIALIZED VIEW {old_obj['matviewname']} RENAME TO {tmp_name}"
                    )

                    try:
                        cursor.execute(
                            f"CREATE MATERIALIZED VIEW {new_obj.matviewname} AS {new_obj.definition}"
                        )
                    except ProgrammingError as e:
                        # no need to rename back the materialized view since the transaction will rollback
                        self.update_state(
                            state=states.FAILURE,
                            meta={
                                "exc_type": type(e).__name__,
                                "exc_message": f"Error while changing the materialized view {new_obj.matviewname} in the underlying database.",
                            },
                            traceback=e,
                        )
                        raise Ignore()

                    cursor.execute(f"DROP MATERIALIZED VIEW {tmp_name}")
                else:
                    raise Ignore()

            else:
                try:
                    cursor.execute(
                        f"CREATE MATERIALIZED VIEW {new_obj.matviewname} AS {new_obj.definition}"
                    )
                except ProgrammingError as e:
                    self.update_state(
                        state=states.FAILURE,
                        meta={
                            "exc_type": type(e).__name__,
                            "exc_message": f"Error while creating the materialized view {new_obj.matviewname} in the underlying database.",
                        },
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
def refresh_materialized_views_task(names):
    refresh(logger, query_set=MaterializedQuery.objects.filter(matviewname__in=names))
