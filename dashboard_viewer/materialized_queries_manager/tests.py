from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import serializers
from django.test import Client, TestCase, TransactionTestCase
from django_celery_results.models import TaskResult

from .models import MaterializedQuery
from .tasks import create_materialized_view


def _init(target):
    target.admin_user = "test_admin"
    target.admin_password = User.objects.make_random_password()
    user, _ = User.objects.get_or_create(username=target.admin_user)
    user.set_password(target.admin_password)
    user.is_staff = user.is_superuser = user.is_active = True
    user.save()

    from django.db import connections  # noqa

    with connections["achilles"].cursor() as cursor:
        for i, name in enumerate(["outlier", "test2", "test3"]):
            cursor.execute(f"DROP MATERIALIZED VIEW IF EXISTS {name}")
            cursor.execute(f"CREATE MATERIALIZED VIEW {name} AS SELECT {i + 1}")


def _login_admin(self):
    client = Client()
    client.login(username=self.admin_user, password=self.admin_password)
    return client


class MaterializedQueryTestCase(TestCase):
    databases = "__all__"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _init(cls)

    def test_single_delete(self):
        client = _login_admin(self)
        client.post(
            "/admin/%s/%s/outlier/delete/"
            % (MaterializedQuery._meta.app_label, MaterializedQuery._meta.model_name),
            data={"post": "yes"},
        )

        self.assertEqual(2, MaterializedQuery.objects.count())
        with self.assertRaises(MaterializedQuery.DoesNotExist):
            MaterializedQuery.objects.get(matviewname="outlier")

    def test_multiple_delete(self):
        client = _login_admin(self)
        client.post(
            "/admin/%s/%s/"
            % (MaterializedQuery._meta.app_label, MaterializedQuery._meta.model_name),
            data={
                "post": "yes",
                "action": "delete_selected",
                "_selected_action": ["test2", "test3"],
            },
        )

        self.assertEqual(1, MaterializedQuery.objects.count())
        try:
            MaterializedQuery.objects.get(matviewname="outlier")
        except MaterializedQuery.DoesNotExist:
            self.fail()

    @patch("materialized_queries_manager.tasks.create_materialized_view.delay")
    def test_add_view(self, create_task):
        client = _login_admin(self)
        client.post(
            "/admin/%s/%s/add/"
            % (MaterializedQuery._meta.app_label, MaterializedQuery._meta.model_name),
            data={"matviewname": "test", "definition": "SELECT"},
        )

        create_task.assert_called_with(
            int(client.session["_auth_user_id"]),
            None,
            serializers.serialize(
                "json", [MaterializedQuery(matviewname="test", definition="SELECT")]
            ),
            [{"added": {}}],
        )

    @patch("materialized_queries_manager.tasks.create_materialized_view.delay")
    def test_change_view(self, create_task):
        """
        should
        - detect that only the definition changed
        - send the correct previous model
        - send the correct new model
        """
        client = _login_admin(self)
        client.post(
            "/admin/%s/%s/outlier/change/"
            % (MaterializedQuery._meta.app_label, MaterializedQuery._meta.model_name),
            data={"matviewname": "outlier", "definition": "SELECT 2"},
        )

        create_task.assert_called_with(
            int(client.session["_auth_user_id"]),
            MaterializedQuery.objects.get(matviewname="outlier").to_dict(),
            serializers.serialize(
                "json",
                [MaterializedQuery(matviewname="outlier", definition="SELECT 2")],
            ),
            [{"changed": {"fields": ["definition"]}}],
        )


class CeleryTasksTestCase(TransactionTestCase):
    databases = "__all__"
    reset_sequences = True

    setUp = _init

    def test_change_celery_valid_definition_change(self):
        task = create_materialized_view.delay(
            int(User.objects.get(username=self.admin_user).id),
            MaterializedQuery.objects.get(matviewname="outlier").to_dict(),
            serializers.serialize(
                "json",
                [MaterializedQuery(matviewname="outlier", definition="SELECT 2")],
            ),
            [{"changed": {"fields": ["definition"]}}],
        )

        task.wait()

        self.assertEqual(3, MaterializedQuery.objects.count())
        self.assertEquals(
            " SELECT 2;",
            MaterializedQuery.objects.get(matviewname="outlier").definition,
        )

    def test_change_celery_invalid_definition_change(self):
        task = create_materialized_view.delay(
            int(User.objects.get(username=self.admin_user).id),
            MaterializedQuery.objects.get(matviewname="outlier").to_dict(),
            serializers.serialize(
                "json",
                [MaterializedQuery(matviewname="outlier", definition="SELECT a")],
            ),
            [{"changed": {"fields": ["definition"]}}],
        )

        task.wait(timeout=None)
        task_results = TaskResult.objects.get(task_id=task.id)

        self.assertEqual("FAILURE", task_results.status)
        self.assertTrue(
            "Error while changing the materialized view outlier in the underlying database."
            in task_results.result
        )
        self.assertEqual(3, MaterializedQuery.objects.count())
        self.assertEquals(
            " SELECT 1;",
            MaterializedQuery.objects.get(matviewname="outlier").definition,
        )

    def test_change_celery_matviewname_change(self):
        task = create_materialized_view.delay(
            int(User.objects.get(username=self.admin_user).id),
            MaterializedQuery.objects.get(matviewname="outlier").to_dict(),
            serializers.serialize(
                "json",
                [MaterializedQuery(matviewname="outlier2", definition=" SELECT 1;")],
            ),
            [{"changed": {"fields": ["matviewname"]}}],
        )

        task.wait(timeout=None)

        self.assertEqual(3, MaterializedQuery.objects.count())
        with self.assertRaises(MaterializedQuery.DoesNotExist):
            MaterializedQuery.objects.get(matviewname="outlier")

        try:
            self.assertEqual(
                " SELECT 1;",
                MaterializedQuery.objects.get(matviewname="outlier2").definition,
            )
        except MaterializedQuery.DoesNotExist:
            self.fail()
        finally:
            from django.db import connections  # noqa

            with connections["achilles"].cursor() as cursor:
                cursor.execute(f"DROP MATERIALIZED VIEW IF EXISTS outlier2")

    def test_valid_create(self):
        task = create_materialized_view.delay(
            int(User.objects.get(username=self.admin_user).id),
            None,
            serializers.serialize(
                "json",
                [MaterializedQuery(matviewname="outlier2", definition="select 1")],
            ),
            [{"added": {}}],
        )

        task.wait(timeout=None)

        self.assertEqual(4, MaterializedQuery.objects.count())

        try:
            self.assertEqual(
                " SELECT 1;",
                MaterializedQuery.objects.get(matviewname="outlier2").definition,
            )
        except MaterializedQuery.DoesNotExist:
            self.fail()
        finally:
            from django.db import connections  # noqa

            with connections["achilles"].cursor() as cursor:
                cursor.execute(f"DROP MATERIALIZED VIEW IF EXISTS outlier2")

    def test_invalid_create(self):
        task = create_materialized_view.delay(
            int(User.objects.get(username=self.admin_user).id),
            None,
            serializers.serialize(
                "json",
                [MaterializedQuery(matviewname="outlier2", definition="select a")],
            ),
            [{"added": {}}],
        )

        task.wait()
        task_results = TaskResult.objects.get(task_id=task.id)

        self.assertEqual("FAILURE", task_results.status)
        self.assertTrue(
            "Error while creating the materialized view outlier2 in the underlying database."
            in task_results.result
        )
        self.assertEqual(3, MaterializedQuery.objects.count())
