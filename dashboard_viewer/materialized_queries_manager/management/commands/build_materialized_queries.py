from contextlib import closing

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import ProgrammingError
from materialized_queries_manager.models import MaterializedQuery


class Command(BaseCommand):

    help = (
        "Generates the materialized queries records as materialized views on Postgres"
    )

    def handle(self, *_, **__):
        with closing(connections["achilles"].cursor()) as cursor:
            for materialized_query in MaterializedQuery.objects.all():

                cursor.execute(
                    "SELECT COUNT(*) FROM pg_matviews WHERE matviewname = %s",
                    [materialized_query.name],
                )
                if cursor.fetchone()[0] > 0:
                    self.stdout.write(
                        f"Materialized view {materialized_query.name} already exists. Skipping.",
                        self.style.WARNING,
                    )
                    continue

                try:
                    cursor.execute(
                        f"CREATE MATERIALIZED VIEW {materialized_query.name} AS {materialized_query.query}"
                    )

                    cursor.execute(
                        f"GRANT SELECT ON {materialized_query.name} TO {settings.POSTGRES_SUPERSET_USER}"
                    )
                except ProgrammingError as e:
                    self.stderr.write(
                        f"Invalid sql on query '{materialized_query.name}'. Skipping. You should edit the sql query "
                        f"under the admin app and the materialized views will be created. Error: {e}",
                        self.style.ERROR,
                    )
