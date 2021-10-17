from django.test import TestCase


class ViewTestClass(TestCase):
    def test_error_page(self):
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, 404)

    def test_404_templete(self):
        response = self.client.get('/nonexist-page/')
        self.assertTemplateUsed(response, 'core/404.html')
