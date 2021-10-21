from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Post

User = get_user_model()


class PostsPagesTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create(username='TestUser')
        cls.user_follow = User.objects.create(username='TestFollow')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client_follow = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_follow.force_login(self.user_follow)

    def test_profile_follow(self):
        """Проверяем, что пользователь может
        подписываться на других пользователей.
        """
        count_follows = Follow.objects.count()

        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={
                    'username': 'TestFollow'})
        )
        count_follows_after_cread = Follow.objects.count()

        self.assertEqual(count_follows_after_cread, count_follows + 1)

    def test_profile_unfollow(self):
        """Проверяем, что пользователь может
        отписываться от других пользователей.
        """
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={
                    'username': 'TestFollow'})
        )
        count_follows = Follow.objects.count()
        self.authorized_client.get(
            reverse('posts:profile_unfollow', kwargs={
                    'username': 'TestFollow'})
        )
        count_follows_after_delete = Follow.objects.count()

        self.assertEqual(count_follows_after_delete, count_follows - 1)

    def test_new_post_in_follow(self):
        """Проверяем, что новая запись пользователя
        появляется в ленте тех, кто на него подписан.
        """
        Follow.objects.create(user=self.user_follow, author=self.user)
        Post.objects.create(
            author=self.user,
            text='Test'
        )

        response = self.authorized_client_follow.get(reverse(
            'post:follow_index')
        )
        count_post = len(response.context['page_obj'])

        self.assertEqual(count_post, 1)

    def test_new_post_in_unfollow(self):
        """Проверяем, что новая запись пользователя
         не появляется в ленте тех, кто на него не подписан.
        """
        Follow.objects.create(user=self.user_follow, author=self.user)
        Post.objects.create(
            author=self.user,
            text='Test'
        )

        response_not_follow = self.authorized_client.get(reverse(
            'post:follow_index')
        )
        count_post = len(response_not_follow.context['page_obj'])

        self.assertEqual(count_post, 0)
