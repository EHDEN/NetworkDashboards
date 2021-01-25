from django.core.validators import RegexValidator
from django.db import models


class MaterializedQuery(models.Model):
    class Meta:
        managed = False
        db_table = "pg_matviews"

    matviewname = models.CharField(
        primary_key=True,
        max_length=100,
        validators=(
            RegexValidator(
                r"^[_0-9a-zA-Z]+$",
                'Only alphanumeric characters and the character "_" are allowed.',
            ),
        ),
        unique=True,
    )
    definition = models.TextField(
        validators=(
            RegexValidator(
                r"--", "Single line comments are not allowed", inverse_match=True
            ),
            RegexValidator(
                r"/\*.*?\*/", "Block comments are not allowed", inverse_match=True
            ),
        )
    )

    def delete(self, using=None, keep_parents=False):
        from django.db import connections  # noqa

        with connections["achilles"].cursor() as cursor:
            cursor.execute("DROP MATERIALIZED VIEW " + self.matviewname)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.matviewname
