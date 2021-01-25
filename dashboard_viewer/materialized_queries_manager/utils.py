from contextlib import closing

from django.core.cache import cache
from django.db import connections
from materialized_queries_manager.models import MaterializedQuery
from redis_rw_lock import RWLock


def refresh(logger, db_id=None):
    # Only one worker can update the materialized views at the same time -> same as -> only one thread
    #  can write to a file at the same time
    write_lock = RWLock(
        cache.client.get_client(), "celery_worker_updating", RWLock.WRITE, expire=None
    )
    write_lock.acquire()

    logger.info(
        "Updating materialized views [%s]",
        "command" if not db_id else f"datasource {db_id}",
    )
    with closing(connections["achilles"].cursor()) as cursor:
        for materialized_query in MaterializedQuery.objects.all():
            try:
                logger.info(
                    "Refreshing materialized view %s [%s]",
                    materialized_query.matviewname,
                    "command" if not db_id else f"datasource {db_id}",
                )
                cursor.execute(
                    f"REFRESH MATERIALIZED VIEW {materialized_query.matviewname}"
                )
            except:  # noqa
                logger.exception(
                    "Some unexpected error happen while refreshing materialized query %s. [%s]",
                    materialized_query.name,
                    "command" if not db_id else f"datasource {db_id}",
                )

    write_lock.release()
