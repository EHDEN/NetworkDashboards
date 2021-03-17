from django.test import override_settings, tag, TestCase


@tag("third-party-app")
@override_settings(ALLOWED_HOSTS=["thisapp.host.com", "mainapp.host.com"])
class UploaderRestrictedAccess(TestCase):
    """
    Assumes the following environment variables values:
      SINGLE_APPLICATION_MODE=n
      MAIN_APPLICATION_HOST=mainapp.host.com
    """

    databases = "__all__"

    def test_block_if_wrong_host(self):
        response = self.client.get("/uploader/test/", HTTP_HOST="thisapp.host.com")

        self.assertEqual(403, response.status_code)

    def test_not_block_if_correct_host(self):
        response = self.client.get("/uploader/test/", HTTP_HOST="mainapp.host.com")

        self.assertEqual(200, response.status_code)
        self.assertTrue(response.has_header("X-Frame-Options"))
        self.assertEqual(
            "ALLOW-FROM HTTPS://MAINAPP.HOST.COM/", response["X-Frame-Options"]
        )

    def test_not_block_other_urls(self):
        response = self.client.get("/admin/login/", HTTP_HOST="thisapp.host.com")

        self.assertEqual(200, response.status_code)
        self.assertTrue(response.has_header("X-Frame-Options"))
        self.assertEqual(
            "ALLOW-FROM HTTPS://MAINAPP.HOST.COM/", response["X-Frame-Options"]
        )


class UploaderNonRestrictedAccess(TestCase):
    """
    Assumes the following environment variables values:
      SINGLE_APPLICATION_MODE=y
    """

    databases = "__all__"

    @override_settings(ALLOWED_HOSTS=["some.domain.com"])
    def test_not_block_if_single_application(self):
        response = self.client.get("/uploader/test/", HTTP_HOST="some.domain.com")

        self.assertEqual(200, response.status_code)
        if response.has_header("X-Frame-Options"):
            self.assertNotIn("ALLOW-FROM ", response.get("X-Frame-Options"))
