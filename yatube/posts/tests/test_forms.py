from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from http import HTTPStatus

from ..models import Post, Group, Comment

import shutil
import tempfile
import os


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User.objects.create_user(username='Sergei')
        cls.author = User.objects.get(username='Sergei')
        image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=image,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            group=Group.objects.create(slug='test-group'),
            author=cls.author,
            image=uploaded
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            text='Текст комментария',
            author=cls.author,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='SergeiSob')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        # Подсчитаем количество записей в Task
        post_count = Post.objects.count()
        # Подготавливаем данные для передачи в форму
        test_text = self.post.text
        group = self.post.group.id
        author = self.post.author.id
        image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=image,
            content_type='image/gif'
        )
        form_data = {
            'text': test_text,
            'group': group,
            'author': author,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post = Post.objects.filter(text=test_text,
                                   group=group,
                                   author=author).first()
        self.assertRedirects(response, reverse('posts:profile',
                                               kwargs={'username': self.user}))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(form_data['text'],
                         post.text,
                         'Текст созданного поста не совпадает')
        self.assertEqual(form_data['group'],
                         post.group.id,
                         'Группа созданного поста не совпадает')
        self.assertEqual(form_data['author'],
                         post.author.id,
                         'Автор созданного поста не совпадает')
        self.assertEqual(form_data['image'].name,
                         os.path.basename(post.image.name),
                         'Картинка созданного поста не совпадает')

    def test_edit_post(self):
        post_count = Post.objects.count()
        test_text = self.post.text
        group = self.post.group.id
        author = self.post.author.id
        image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=image,
            content_type='image/gif'
        )
        form_data = {
            'text': test_text,
            'group': group,
            'author': author,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        post = Post.objects.filter(text=test_text).first()
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.id}))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(form_data['text'],
                         post.text,
                         'Текст созданного поста не совпадает')
        self.assertEqual(form_data['group'],
                         post.group.id,
                         'Группа созданного поста не совпадает')
        self.assertEqual(form_data['author'],
                         post.author.id,
                         'Автор созданного поста не совпадает')
        self.assertEqual(form_data['image'].name,
                         os.path.basename(post.image.name),
                         'Картинка созданного поста не совпадает')

    def test_create_post_guest(self):
        """Валидная форма создает запись в Post."""
        # Подсчитаем количество записей в Task
        post_count = Post.objects.count()
        # Подготавливаем данные для передачи в форму
        test_text = self.post.text
        group = self.post.group

        form_data = {
            'text': test_text,
            'group': group
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, (reverse('users:login')
                                        + '?next='
                                        + reverse('posts:post_create')))
        self.assertEqual(Post.objects.count(), post_count)

    def test_comment_post_authorized(self):
        """Валидная форма создает коммент к посту."""
        comment = Comment.objects.count()
        comm_text = self.comment.text
        author = self.comment.author.id
        form_data = {
            'text': comm_text,
            'author': author,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        comm = Comment.objects.filter(text=comm_text).first()
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.id}))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), comment + 1)
        self.assertEqual(form_data['text'],
                         comm.text,
                         'Текст созданного комменатрия не совпадает')

    def test_comment_post_guest(self):
        """Валидная форма создает комментарий к посту для гостевого юзера."""
        comment = Comment.objects.count()
        comm_text = self.comment.text
        author = self.comment.author.id
        form_data = {
            'text': comm_text,
            'author': author,
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             (reverse('users:login')
                              + '?next='
                              + reverse('posts:add_comment',
                                        kwargs={'post_id': self.post.id})))
        self.assertEqual(Comment.objects.count(), comment)
