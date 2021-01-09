from contextlib import closing

from django.core.cache import cache
from django.db import connections, ProgrammingError
from redis_rw_lock import RWLock

from materialized_queries_manager.models import MaterializedQuery


def refresh(logger, db_id=None):
    # Only one worker can update the materialized views at the same time -> same as -> only one thread
    #  can write to a file at the same time
    write_lock = RWLock(
        cache.client.get_client(), "celery_worker_updating", RWLock.WRITE, expire=None
    )
    write_lock.acquire()

    logger.info("Updating materialized views [%s]", "command" if db_id else f"datasource {db_id}")
    with closing(connections["achilles"].cursor()) as cursor:
        for materialized_query in MaterializedQuery.objects.all():
            try:
                logger.info(
                    f"Refreshing materialized view %s [%s]",
                    materialized_query.name,
                    "command" if db_id else f"datasource {db_id}",
                )
                cursor.execute(f"REFRESH MATERIALIZED VIEW {materialized_query.name}")
            except ProgrammingError:
                # If this happen, it is assumed its because the there is no materialized views
                #  created on postgres with the given name
                # TODO Log this or give some feed back on the Materialized query list, on admin app, if any
                #  record doesn't have a materialized view associated.
                pass  # Ignore if the view doesn't exist
            except:  # noqa
                logger.exception(
                    "Some unexpected error happen while refreshing materialized query %s. [%s]",
                    materialized_query.name,
                    "command" if db_id else f"datasource {db_id}",
                )

    write_lock.release()
