
from contextlib import closing

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import connections, models
from django.db.utils import ProgrammingError


class MaterializedQuery(models.Model):
    name = models.CharField(max_length=20, validators=(
        RegexValidator(r'^[_0-9a-zA-Z]+$', 'Only alphanumeric characters and the character "_" are allowed.'),
    ))
    query = models.TextField(validators=(
        RegexValidator(r'--', "Single line comments are not allowed", inverse_match=True),
        RegexValidator(r'/\*.*?\*/', "Block comments are not allowed", inverse_match=True),
        RegexValidator(r';', "';' characters are not allowed", inverse_match=True),
    ))

    def _create_materialized_view(self, cursor):
        try:
            cursor.execute(f"CREATE MATERIALIZED VIEW {self.name} AS {self.query}")
        except ProgrammingError as e:
            raise ValidationError("Invalid query. " + str(e))

        cursor.execute(f"GRANT SELECT ON {self.name} TO {settings.POSTGRES_SUPERSET_USER}")

    def full_clean(self, exclude=None, validate_unique=True):
        super().full_clean(exclude, validate_unique)

        with closing(connections["achilles"].cursor()) as cursor:
            if self.id:
                old = MaterializedQuery.objects.get(id=self.id)
                if old.name != self.name and old.query == self.query:
                    cursor.execute(f"ALTER MATERIALIZED VIEW {old.name} RENAME TO {self.name}")
                elif old.query != self.query:
                    cursor.execute(f"DROP MATERIALIZED VIEW {old.name}")
                    self._create_materialized_view(cursor)

            else:
                self._create_materialized_view(cursor)

    def delete(self, using=None, keep_parents=False):
        super().delete(using, keep_parents)

        with closing(connections["achilles"].cursor()) as cursor:
            cursor.execute(f"DROP MATERIALIZED VIEW {self.name}")
