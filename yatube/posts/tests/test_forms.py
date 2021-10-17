import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = PostForm()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.user = User.objects.create(username='TestUser')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test',
            group=PostsFormsTests.group
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.form_data = {
            'author': cls.post.author,
            'text': 'Тестовый текст',
            'group': cls.group.pk,
        }
        cls.form_data_no_group = {
            'author': cls.post.author,
            'text': 'Тестовый текст'
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """
        Проверяем, при отправке валидной формы со страницы создания поста
        происходит редирект, создаётся новая запись в базе данных,
        группа и автор такие же как мы ожидаем.
        """
        post_count = Post.objects.count()

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )

        self.assertRedirects(
            response, reverse('posts:profile', kwargs={'username': 'TestUser'})
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                group=self.group.pk,
                author=self.post.author
            ).exists()
        )

    def test_create_post_no_group(self):
        """
        Проверяем, при отправке валидной формы со страницы создания поста
        без группы происходит редирект, создаётся новая запись в базе данных,
        группа и автор такие же как мы ожидаем.
        """
        post_count = Post.objects.count()

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form_data_no_group,
            follow=True
        )

        self.assertRedirects(
            response, reverse('posts:profile', kwargs={'username': 'TestUser'})
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                author=self.post.author,
                group=None
            ).exists()
        )

    def test_edit_post(self):
        """
        Проверяем, при отправке валидной формы со страницы редоктирования поста
        происходит редирект,изменение поста с post_id в базе данных,
        группа и автор такие же как мы ожидаем.
        """
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=self.form_data,
            follow=True
        )

        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertTrue(
            Post.objects.filter(
                author=self.post.author,
                text='Тестовый текст',
                group=self.group.pk
            ).exists()
        )

    def test_edit_post_no_group(self):
        """
        Проверяем, при отправке валидной формы со страницы редоктирования поста
        без группы происходит редирект, изменение поста с post_id
        в базе данных, группа и автор такие же как мы ожидаем.
        """
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=self.form_data_no_group,
            follow=True
        )

        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertTrue(
            Post.objects.filter(
                author=self.post.author,
                text='Тестовый текст',
                group=None
            ).exists()
        )

    def test_create_post_with_image(self):
        """
        Проверяем, при отправке валидной формы со страницы создания поста
        происходит редирект, создание поста с картинкой
        в базе данных.
        """
        posts_count = Post.objects.count()
        form_data = {
            'author': self.post.author,
            'text': 'Тестовый текст',
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:profile', kwargs={'username': 'TestUser'})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.first()
        self.assertEqual(post.image, 'posts/small.gif')

    def test_create_commen(self):
        """
        Проверяем, что при создание комментарий появляется на странице поста.
        """
        comment_count = Comment.objects.count()
        form_data = {'text': 'Тестовый текст'}

        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )

        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text='Тестовый текст',).exists()
        )
