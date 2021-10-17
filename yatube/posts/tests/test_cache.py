from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post

User = get_user_model()


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_page_cache(self):
        """Проверяем  работу кеша."""
        response = self.authorized_client.get(
            reverse('posts:index')).content
        first_response = self.authorized_client.get(
            reverse('posts:index')).content

        self.assertEqual(response, first_response)

        Post.objects.get(id=self.post.id).delete()
        second_response = self.authorized_client.get(
            reverse('posts:index')).content

        self.assertEqual(response, second_response)

        cache.clear()
        third_responce = self.authorized_client.get(
            reverse('posts:index')).content

        self.assertNotEqual(response, third_responce)
