from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class AboutURLTests(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_home_url_exists_at_desired_location(self):
        """URL-адрес доступен всем."""
        url_names = (
            '/about/author/',
            '/about/tech/'
        )

        for adress in url_names:
            with self.subTest(adress=adress):

                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)
