from http import HTTPStatus

from django.test import TestCase


class ErrorTestClass(TestCase):
    def test_error_page(self):
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_404_templete(self):
        response = self.client.get('/nonexist-page/')
        self.assertTemplateUsed(response, 'core/404.html')
