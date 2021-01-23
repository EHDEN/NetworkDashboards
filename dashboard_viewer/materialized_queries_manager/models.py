from contextlib import closing

from django.core.validators import RegexValidator
from django.db import connections, models, ProgrammingError
from django.db.models.signals import post_delete
from django.dispatch import receiver


class MaterializedQuery(models.Model):
    name = models.CharField(
        max_length=100,
        validators=(
            RegexValidator(
                r"^[_0-9a-zA-Z]+$",
                'Only alphanumeric characters and the character "_" are allowed.',
            ),
        ),
        unique=True,
    )
    dashboards = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="In which dashboards is the view being used. This is field is Optional "
        "field and has the intent to help on organization and search among the "
        "different queries.",
    )
    query = models.TextField(
        validators=(
            RegexValidator(
                r"--", "Single line comments are not allowed", inverse_match=True
            ),
            RegexValidator(
                r"/\*.*?\*/", "Block comments are not allowed", inverse_match=True
            ),
            RegexValidator(r";", "';' characters are not allowed", inverse_match=True),
        )
    )

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.name


@receiver(post_delete, sender=MaterializedQuery)
def drop_materialized_view(sender, **kwargs):  # noqa
    instance = kwargs["instance"]
    with closing(connections["achilles"].cursor()) as cursor:
        try:
            cursor.execute(f"DROP MATERIALIZED VIEW {instance.name}")
        except ProgrammingError:
            pass  # Ignore if the view doesn't exist
