import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-slug'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test',
            group=cls.group
        )
        Post.objects.bulk_create([
            Post(author=cls.user, text='Test_text', group=cls.group)
            for _ in range(12)
        ])
        cls.group_nod_includ_post = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-slug_nod_includ_post'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_posts', kwargs={'slug': 'test-slug'}):
            'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': 'TestUser'}):
            'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={
                    'post_id': self.post.pk}):
                    'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={
                    'post_id': self.post.pk}):
                    'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('users:login'): 'users/login.html',
            reverse('users:logout'): 'users/logged_out.html',
            reverse('users:signup'): 'users/signup.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)

                self.assertTemplateUsed(response, template)

    def test_first_page_contains_ten_records(self):
        """Проверяем, что паджинатор выводит 10 записей на страницу."""
        reverse_dict_for_paginator_test = [
            reverse('post:index'),
            reverse('posts:group_posts', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'TestUser'})
        ]

        for reverse_name in reverse_dict_for_paginator_test:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)

                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """Проверяем, что паджинатор выводит 3 записей на вторую страницу."""
        reverse_dict_for_paginator_test = [
            reverse('post:index') + '?page=2',
            reverse(
                'posts:group_posts', kwargs={'slug': 'test-slug'}) + '?page=2',
            reverse(
                'posts:profile', kwargs={'username': 'TestUser'}) + '?page=2'
        ]

        for reverse_name in reverse_dict_for_paginator_test:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)

                self.assertEqual(len(response.context['page_obj']), 3)

    def test_context_index(self):
        """Проверяем, что context передает список постов."""
        response = self.authorized_client.get(reverse('post:index'))

        for post in response.context['page_obj']:
            self.assertIsInstance(post, Post)

    def test_context_group_list(self):
        """
        Проверяем, что context передает список постов отфильтрованых по группе.
        """
        response = self.authorized_client.get(
            reverse(
                'posts:group_posts', kwargs={'slug': 'test-slug'}))

        for post in response.context['page_obj']:
            self.assertEqual(post.group, self.group)

    def test_context_profile(self):
        """
        Проверяем, что context передает
        список постов отфильтрованых по пользователю.
        """
        response = self.authorized_client.get(
            reverse(
                'posts:profile', kwargs={'username': 'TestUser'}))

        for post in response.context['page_obj']:
            self.assertEqual(post.author, self.user)

    def test_context_post_detail(self):
        """
        Проверяем, что context передает пост отфильтрованый по id.
        """
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}))
        test_pk = response.context['post'].pk
        self.assertEqual(test_pk, self.post.pk)

    def test_context_post_edit(self):
        """
        Проверяем, что context передает форму
        редоктирования поста отфильтрованного по id.
        """
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={
                    'post_id': self.post.pk})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_context_post_creat(self):
        """Проверяем, что context передает форму создания поста."""
        response = self.authorized_client.get(
            reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)

                self.assertIsInstance(form_field, expected)

    def test_post_new_create(self):
        """
        Проверяем, что если при создании поста указать группу,
        то этот пост появляется на главной странице,
        на странице выбранной группы,в профайле пользователя.
        """
        post_creat = Post.objects.create(
            author=self.user,
            text='Test',
            group=self.group
        )
        expected_pages = [
            reverse('posts:index'),
            reverse(
                'posts:group_posts', kwargs={'slug': 'test-slug'}),
            reverse(
                'posts:profile', kwargs={'username': 'TestUser'})
        ]

        for reverse_name in expected_pages:
            with self.subTest(revers_name=reverse_name):
                response = self.authorized_client.get(reverse_name)

                self.assertIn(
                    post_creat, response.context['page_obj']
                )

    def test_post_new_not_in_group(self):
        """
        Проверяем, что этот пост не попал в группу,
        для которой не был предназначен.
        """
        post_creat = Post.objects.create(
            author=self.user,
            text='Test',
            group=self.group
        )

        response = self.authorized_client.get(
            reverse(
                'posts:group_posts',
                kwargs={'slug': 'test-slug_nod_includ_post'})
        )

        self.assertNotIn(
            post_creat, response.context['page_obj']
        )

    def test_context_with_image_in_post_detail(self):
        """
        Проверяем, что при выводе поста с картинкой, изображение
        передаётся в словаре context post_detail.
        """
        gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='gif',
            content=gif,
            content_type='image/gif'
        )
        post = Post.objects.create(
            author=self.user,
            text='Test',
            image=uploaded,
            group=self.group
        )

        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={
                    'post_id': post.pk})
        )
        first_object = response.context.get('post')

        self.assertEqual(first_object.author, post.author)
        self.assertEqual(first_object.image, 'posts/gif')
        self.assertEqual(first_object.text, post.text)
        self.assertEqual(first_object.group, post.group)

    def test_context_with_image(self):
        """
        Проверяем, что при выводе поста с картинкой, изображение
        передаётся в словаре context.
        """
        image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='image',
            content=image,
            content_type='image/gif'
        )
        post = Post.objects.create(
            author=self.user,
            text='Test',
            image=uploaded,
            group=self.group
        )
        url_names = (
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': 'TestUser'}),
            reverse('posts:group_posts', kwargs={'slug': 'test-slug'}),
        )

        for adress in url_names:
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                first_object = response.context['page_obj'][0]

                self.assertEqual(first_object.author, post.author)
                self.assertEqual(first_object.image, post.image)
                self.assertEqual(first_object.text, post.text)
                self.assertEqual(first_object.group, post.group)

    def test_comment_posts_only_authorized_user(self):
        """
        Проверяем, что комментировать посты
        может только авторизованный пользователь.
        """
        comment_count = Comment.objects.count()
        form_data = {'text': 'Тестовый текст'}

        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )

        self.assertEqual(Comment.objects.count(), comment_count)
