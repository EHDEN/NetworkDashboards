import json
import os
from unittest.mock import patch

from django.test import Client, TestCase
from uploader import models as uploader_models

from . import models
from .tasks import send_updates


class NoActiveRequestGroupsTestCase(TestCase):
    databases = "__all__"

    fixtures = ("base", "not_active")

    @classmethod
    def setUpClass(cls):
        super(NoActiveRequestGroupsTestCase, cls).setUpClass()
        cls.client = Client()

    def _upload_and_check(self):
        with open(
            f"{os.path.dirname(__file__)}/fixtures/achilles_results_dist.csv"
        ) as fp:
            self.client.post("/uploader/test/", {"results_file": fp}, follow=True)

        self.assertEqual(0, models.RequestLog.objects.count())
        self.assertEqual(0, models.RequestsGroupLog.objects.count())
        self.assertEqual(1, uploader_models.UploadHistory.objects.count())

    @patch("uploader.tasks.update_achilles_results_data.delay")
    def test_exist_but_not_active(self, _):
        self._upload_and_check()

    @patch("uploader.tasks.update_achilles_results_data.delay")
    def test_none(self, _):
        models.RequestsGroup.objects.all().delete()

        self._upload_and_check()


class BaseInitialDataTestCase(TestCase):
    databases = "__all__"

    fixtures = ("base", "active", "data")

    @staticmethod
    def _generate_json_data():
        data = uploader_models.AchillesResults.objects.all()
        key_to_exclude = ("_state", "id", "data_source_id")
        data = [
            {k: v for k, v in record.__dict__.items() if k not in key_to_exclude}
            for record in data
        ]

        return json.dumps(data)


class LogsTestCase(BaseInitialDataTestCase):
    def _execute_and_check(self, error_message_portion, render_empty=False):
        task = send_updates.delay(1, 1, self._generate_json_data())
        task.wait(timeout=None)

        self.assertEqual(1, models.RequestsGroupLog.objects.count())
        group_log = models.RequestsGroupLog.objects.get()
        self.assertEqual(0, group_log.success_count)

        self.assertEqual(1, models.RequestLog.objects.count())
        failed_request_log = models.RequestLog.objects.get()
        self.assertFalse(failed_request_log.success)
        if render_empty:
            self.assertIsNone(failed_request_log.request_arguments_template_render)
        else:
            self.assertIsNotNone(failed_request_log.request_arguments_template_render)
        self.assertIsNotNone(failed_request_log.exception)
        self.assertIn(error_message_portion, failed_request_log.exception)

    def test_invalid_json_render(self):
        first_request = models.Request.objects.get(order=1)
        first_request.request_arguments_template = (
            first_request.request_arguments_template[1:]
        )
        first_request.save()

        self._execute_and_check("JSONDecodeError")

    def test_missing_required_parameters(self):
        first_request = models.Request.objects.get(order=1)
        first_request.request_arguments_template = '{"method": "get","data": {"patient_count": "{{ achilles_results.0.0.count_value }}"}}'
        first_request.save()

        self._execute_and_check("missing 1 required positional argument")

    @patch("requests.Session.request")
    def test_invalid_condition_expression(self, _):
        first_request = models.Request.objects.get(order=1)
        first_request.success_condition_template = "def function():"
        first_request.save()

        self._execute_and_check("SyntaxError: invalid syntax")

    def test_invalid_template(self):
        first_request = models.Request.objects.get(order=1)
        first_request.request_arguments_template = "{{ asdf }"
        first_request.save()

        self._execute_and_check("TemplateSyntaxError", render_empty=True)


class ContextsAvailableTestCase(BaseInitialDataTestCase):
    @patch("requests.Session.request")
    def test_previous_answers_available(self, session_request):
        session_request.return_value.text = "LAST_RESPONSE_CONTENT"

        task = send_updates.delay(1, 1, self._generate_json_data())
        task.wait(timeout=None)

        self.assertEqual(1, models.RequestsGroupLog.objects.count())
        group_log = models.RequestsGroupLog.objects.get()
        self.assertEqual(2, group_log.success_count)
        requests_logs = group_log.requests
        self.assertEqual(2, requests_logs.count())

        first_request_log = requests_logs.get(request__order=1)
        self.assertTrue(first_request_log.success)
        self.assertIsNone(first_request_log.exception)
        self.assertIsNotNone(first_request_log.request_arguments_template_render)

        second_request_log = requests_logs.get(request__order=2)
        self.assertTrue(second_request_log.success)
        self.assertIsNone(second_request_log.exception)
        self.assertIsNotNone(second_request_log.request_arguments_template_render)
        self.assertIn(
            "LAST_RESPONSE_CONTENT",
            second_request_log.request_arguments_template_render,
        )

    @patch("requests.Session.request")
    def test_response_available(self, session_request):
        session_request.return_value.status_code = 400

        first_request = models.Request.objects.get(order=1)
        first_request.success_condition_template = "{{ response.status_code }} == 200"
        first_request.save()

        task = send_updates.delay(1, 1, self._generate_json_data())
        task.wait(timeout=None)

        self.assertEqual(1, models.RequestsGroupLog.objects.count())
        group_log = models.RequestsGroupLog.objects.get()
        self.assertEqual(0, group_log.success_count)
        requests_logs = group_log.requests
        self.assertEqual(1, requests_logs.count())

        first_request_log = requests_logs.get(request__order=1)
        self.assertIsNotNone(first_request_log.success_condition_template_render)
        self.assertIn("400 == 200", first_request_log.success_condition_template_render)


class SuccessConditionTestSuit(BaseInitialDataTestCase):
    @patch("requests.Session.request")
    def test_stop_on_failed_success_condition(self, session_request):
        session_request.return_value.status_code = 400

        first_request = models.Request.objects.get(order=1)
        first_request.success_condition_template = "{{ response.status_code }} == 200"
        first_request.save()

        task = send_updates.delay(1, 1, self._generate_json_data())
        task.wait(timeout=None)

        self.assertEqual(1, models.RequestsGroupLog.objects.count())
        group_log = models.RequestsGroupLog.objects.get()
        self.assertEqual(0, group_log.success_count)
        requests_logs = group_log.requests
        self.assertEqual(1, requests_logs.count())

        request_log = requests_logs.get(request__order=1)
        self.assertFalse(request_log.success)
        self.assertIsNotNone(request_log.request_arguments_template_render)
        self.assertIsNotNone(request_log.success_condition_template_render)
        self.assertIsNotNone(request_log.exception)
        self.assertIn("Success condition not met", request_log.exception)

    @patch("requests.Session.request")
    def test_exec_all_if_good_condition(self, session_request):
        session_request.return_value.status_code = 200

        first_request = models.Request.objects.get(order=1)
        first_request.success_condition_template = "{{ response.status_code }} == 200"
        first_request.save()

        task = send_updates.delay(1, 1, self._generate_json_data())
        task.wait(timeout=None)

        self.assertEqual(1, models.RequestsGroupLog.objects.count())
        group_log = models.RequestsGroupLog.objects.get()
        self.assertEqual(2, group_log.success_count)
        requests_logs = group_log.requests
        self.assertEqual(2, requests_logs.count())

        for i, request_log in enumerate(requests_logs.all()):
            self.assertTrue(request_log.success)
            self.assertIsNotNone(request_log.request_arguments_template_render)
            if i == 0:
                self.assertIsNotNone(request_log.success_condition_template_render)
            else:
                self.assertIsNone(request_log.success_condition_template_render)
            self.assertIsNone(request_log.exception)
