from django.core.cache import caches
from django.db import connections
from redis_rw_lock import RWLock
import constance
from materialized_queries_manager.models import MaterializedQuery


def refresh(logger, db_id=None, query_set=None):
    cache = caches["workers_locks"]

    # Only one worker can update the materialized views at the same time -> same as -> only one thread
    #  can write to a file at the same time
    with RWLock(
        cache.client.get_client(), "celery_worker_updating", RWLock.WRITE, expire=None
    ):
        logger.info(
            "Updating materialized views [%s]",
            "command" if not db_id else f"datasource {db_id}",
        )

        with connections["achilles"].cursor() as cursor:
            to_refresh = MaterializedQuery.objects.all() if not query_set else query_set
            total = len(to_refresh)

            for i, materialized_query in enumerate(to_refresh):
                try:
                    cursor.execute("SET statement_timeout = " + str(constance.config.REFRESH_MATERIALIZED_TIMEOUT) + ";")
                    logger.info(
                        "Refreshing materialized view %s (%d/%d) [%s]",
                        materialized_query.matviewname,
                        i + 1,
                        total,
                        "command" if not db_id else f"datasource {db_id}",
                    )
                    cursor.execute(
                        f"REFRESH MATERIALIZED VIEW {materialized_query.matviewname}"
                    )
                except:  # noqa
                    logger.exception(
                        "Some unexpected error happen while refreshing materialized query %s. [%s]",
                        materialized_query.matviewname,
                        "command" if not db_id else f"datasource {db_id}",
                    )
