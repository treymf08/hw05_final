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

    def test_profile_unfollow(self):
        """Проверяем, что пользователь может
        подписываться и отписываться от других пользователей.
        """
        count_follows = Follow.objects.count()
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={
                    'username': 'TestFollow'})
        )
        count_follows_after_cread = Follow.objects.count()

        self.assertEqual(count_follows_after_cread, count_follows + 1)

        self.authorized_client.get(
            reverse('posts:profile_unfollow', kwargs={
                    'username': 'TestFollow'})
        )
        count_follows_after_delete = Follow.objects.count()

        self.assertEqual(count_follows_after_delete, count_follows)

    def test_new_post_in_follow_(self):
        """Проверяем, что новая запись пользователя
        появляется в ленте тех, кто на него подписан
        и не появляется в ленте тех, кто не подписан."""
        Follow.objects.create(user=self.user, author=self.user_follow)
        Post.objects.create(
            author=self.user_follow,
            text='Test'
        )

        response = self.authorized_client.get(reverse(
            'post:follow_index')
        )
        count_post = len(response.context['page_obj'])

        self.assertEqual(count_post, 1)

        response_not_follow = self.authorized_client_follow.get(reverse(
            'post:follow_index')
        )
        count_post_not_follow = len(response_not_follow.context['page_obj'])

        self.assertEqual(count_post_not_follow, 0)
