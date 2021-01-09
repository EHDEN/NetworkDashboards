
from django.core.cache import cache
from django.core.management.base import BaseCommand
from materialized_queries_manager.utils import refresh

import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        if cache.get("celery_workers_updating") == 0:
            refresh(logger)
            logger.info("Refresh done [command]")
        else:
            logger.info("Refresh in progress by another worker [command]")
