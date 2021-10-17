from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')
        cls.user_not_author = User.objects.create(
            username='TestUser_not_author'
        )
        cls.post = Post.objects.create(
            author=cls.user,
        )
        Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-slug'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client_user_not_author = Client()
        self.authorized_client_user_not_author.force_login(
            self.user_not_author
        )
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_home_url_exists_at_desired_location(self):
        """URL-адрес доступен всем."""
        url_names = (
            '/',
            '/group/test-slug/',
            '/profile/TestUser/',
            '/posts/1/'
        )

        for adress in url_names:
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)

                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create(self):
        """URL-адрес доступен авторизованному пользователю."""
        response = self.authorized_client_user_not_author.get('/create/')

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_post_id_edit(self):
        """URL-адрес доступен автору."""
        response = self.authorized_client.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexpected_page(self):
        """Не существующий URL-адрес возращает ошибку 404."""
        response = self.guest_client.get('/unexpected_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/TestUser/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html'
        }

        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)

                self.assertTemplateUsed(response, template)
