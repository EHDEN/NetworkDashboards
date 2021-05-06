from django.db import connections, router, transaction
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .models import AchillesResults, AchillesResultsDraft, DataSource
from .utils import move_achilles_results_records


@receiver(pre_save, sender=DataSource)
def set_draft_change(instance, **kwargs):
    """
    Since the save method can fail, here just check if the draft field changed
    """
    if instance.id is not None:
        instance._draft_change = DataSource.objects.get(id=instance.id).draft != instance.draft
    else:
        instance._draft_change = False


@receiver(post_save, sender=DataSource)
def handle_draft_change(instance, **kwargs):
    """
    If the save method didn't fail this will be executed
    """
    if instance._draft_change:
        with transaction.atomic(
            using=router.db_for_write(AchillesResults)
        ), connections["achilles"].cursor() as cursor:
            if instance.draft:
                move_achilles_results_records(
                    cursor, AchillesResults, AchillesResultsDraft, instance.id
                )
            else:
                move_achilles_results_records(
                    cursor, AchillesResultsDraft, AchillesResults, instance.id
                )
