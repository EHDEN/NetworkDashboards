import random
import string
from contextlib import closing

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import connections, models
from django.db.utils import ProgrammingError


class MaterializedQuery(models.Model):
    name = models.CharField(
        max_length=100,
        validators=(
            RegexValidator(
                r"^[_0-9a-zA-Z]+$",
                'Only alphanumeric characters and the character "_" are allowed.',
            ),
        ),
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

    def _create_materialized_view(self, cursor):
        try:
            cursor.execute(f"CREATE MATERIALIZED VIEW {self.name} AS {self.query}")
        except ProgrammingError as e:
            raise ValidationError("Invalid query. " + str(e))

        cursor.execute(
            f"GRANT SELECT ON {self.name} TO {settings.POSTGRES_SUPERSET_USER}"
        )

    def full_clean(self, exclude=None, validate_unique=True):
        super().full_clean(exclude, validate_unique)

        with closing(connections["achilles"].cursor()) as cursor:
            if self.id:
                old = MaterializedQuery.objects.get(id=self.id)

                cursor.execute(
                    "SELECT COUNT(*) FROM pg_matviews WHERE matviewname = %s",
                    [old.name],
                )
                old_exists = cursor.fetchone()[0] > 0

                if not old_exists:
                    self._create_materialized_view(cursor)
                elif old.name != self.name and old.query == self.query:
                    cursor.execute(
                        f"ALTER MATERIALIZED VIEW {old.name} RENAME TO {self.name}"
                    )
                elif old.query != self.query:
                    # don't drop the old view yet. rename the view to a random name
                    #  just as a backup if there is something wrong with the new
                    #  query or name
                    allowed_characters = string.ascii_letters + string.digits + "_"
                    tmp_name = "".join(
                        random.choice(allowed_characters) for _ in range(30)
                    )

                    cursor.execute(
                        f"ALTER MATERIALIZED VIEW {old.name} RENAME TO {tmp_name}"
                    )

                    try:
                        self._create_materialized_view(cursor)
                    except ValidationError as e:
                        cursor.execute(
                            f"ALTER MATERIALIZED VIEW {tmp_name} RENAME TO {old.name}"
                        )
                        raise e

                    cursor.execute(f"DROP MATERIALIZED VIEW {tmp_name}")

            else:
                self._create_materialized_view(cursor)

    def delete(self, using=None, keep_parents=False):
        super().delete(using, keep_parents)

        with closing(connections["achilles"].cursor()) as cursor:
            cursor.execute(f"DROP MATERIALIZED VIEW {self.name}")

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.name
