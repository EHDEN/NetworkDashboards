from contextlib import closing

from django.core.validators import RegexValidator
from django.db import connections, models


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

    def delete(self, using=None, keep_parents=False):
        super().delete(using, keep_parents)

        with closing(connections["achilles"].cursor()) as cursor:
            cursor.execute(f"DROP MATERIALIZED VIEW {self.name}")

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.name
