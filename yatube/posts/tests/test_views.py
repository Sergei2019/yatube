from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache
from django import forms

from ..models import Follow, Group, Post

from collections.abc import Iterable

from http import HTTPStatus

from typing import Iterable

import math


User = get_user_model()

PAG_FIRST_PAGE = 10

FOUND = HTTPStatus.FOUND


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(slug='test-group')
        cls.author = User.objects.create_user(username='Sergei')
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
            author=cls.author,
            group=cls.group,
            image=uploaded
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.get(username='Sergei')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def _test_correct_context_post(self,
                                   url,
                                   kwargs,
                                   post,
                                   context):
        response = self.authorized_client.get(reverse(url, kwargs=kwargs))
        if isinstance(response.context[context], Iterable):
            first_object = response.context[context][0]
        else:
            first_object = response.context[context]
        dict_fields = {
            'text': first_object.text,
            'author': first_object.author,
            'group': first_object.group,
            'image': first_object.image
        }
        for k, v in dict_fields.items():
            if k in vars(post):
                self.assertEqual(v, vars(post)[k])

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        post_id = PostPagesTests.post.id
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.post.group.slug}):
                        'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.post.author.username}):
                        'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': post_id}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': post_id}): 'posts/create_post.html'
        }

        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        self._test_correct_context_post('posts:index',
                                        {},
                                        self.post,
                                        'page_obj')

    def test_profile_page_show_correct_context(self):
        self._test_correct_context_post('posts:profile',
                                        {'username': self.post.author},
                                        self.post,
                                        'page_obj')

    def test_profile_page_show_correct_context(self):
        """Шаблон post detail сформирован с правильным контекстом."""
        self._test_correct_context_post('posts:post_detail',
                                        {'post_id': self.post.id},
                                        self.post,
                                        'post')

    def test_group_page_show_correct_context(self):
        """Шаблон group page сформирован с правильным контекстом."""
        self._test_correct_context_post('posts:group_list',
                                        {'slug': self.post.group.slug},
                                        self.post,
                                        'page_obj')

    def test_edit_post_show_correct_context(self):
        """Шаблон edit сформирован с правильным контекстом."""
        response = (self.authorized_client.
                    get(reverse('posts:post_edit',
                        kwargs={'post_id': self.post.id})))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_cache_index(self):
        response = self.authorized_client.get(reverse('posts:index'))
        Post.objects.get(text=self.post.text,
                         author=self.post.author,
                         group=self.post.group).delete()
        self.assertIn(self.post.text, response.content.decode('utf-8'))
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotIn(self.post.text, response.content.decode('utf-8'))


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='Sergei')
        cls.group = Group.objects.create(slug='test-group')
        cls.list_post = [Post(text=f'Тестовый текст_{i}',
                              author=User.objects.get(username='Sergei'),
                              group=Group.objects.get(slug='test-group')
                              ) for i in range(0, 14)]
        Post.objects.bulk_create(cls.list_post)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def _pages_obj_count(self, page_number):
        num_of_pages = math.ceil(len(self.list_post) / PAG_FIRST_PAGE)
        if page_number != num_of_pages:
            return PAG_FIRST_PAGE
        return len(self.list_post) - (num_of_pages - 1) * PAG_FIRST_PAGE

    def test_first_page_contains_ten_records(self):
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), PAG_FIRST_PAGE)

    def test_second_page_contains_four_records(self):
        page_number = 2
        response = self.client.get(reverse('posts:index')
                                   + f'?page={page_number}')
        self.assertEqual(len(response.context['page_obj']),
                         self._pages_obj_count(page_number))

    def test_group_contains_ten_records(self):
        response = (self.guest_client.
                    get(reverse('posts:group_list',
                        kwargs={'slug': self.group.slug})))
        self.assertEqual(len(response.context['page_obj']), PAG_FIRST_PAGE)

    def test_group_second_page_contains_four_records(self):
        page_number = 2
        response = (self.client.
                    get(reverse('posts:group_list',
                                kwargs={'slug': self.group.slug})
                        + f'?page={page_number}'))
        self.assertEqual(len(response.context['page_obj']),
                         self._pages_obj_count(page_number))

    def test_profile_contains_ten_records(self):
        response = (self.guest_client.
                    get(reverse('posts:profile',
                        kwargs={'username': self.author.username})))
        self.assertEqual(len(response.context['page_obj']), PAG_FIRST_PAGE)

    def test_profile_second_page_contains_ten_records(self):
        page_number = 2
        response = (self.guest_client.
                    get(reverse('posts:profile',
                        kwargs={'username':
                                self.author.username})
                        + f'?page={page_number}'))
        self.assertEqual(len(response.context['page_obj']),
                         self._pages_obj_count(page_number))


class SubscriptionTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(slug='test-group')
        cls.author = User.objects.create_user(username='SergeiSob')

    def setUp(self):
        self.user = User.objects.get(username='SergeiSob')
        self.another_user = User.objects.create_user(username='Serj')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.another_client = Client()
        self.another_client.force_login(self.another_user)

    def _test_subscr(self, url):
        follower_before = Follow.objects.filter(user=self.another_user,
                                                author=self.user).count()
        response = self.another_client.get(
            reverse(url, kwargs={'username': self.user.username}))
        follower_after = Follow.objects.filter(user=self.another_user,
                                               author=self.user).count()
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(abs(follower_after - follower_before), 1)

    def test_auth_subscription(self):
        self._test_subscr('posts:profile_follow')

    def test_auth_unsubscription(self):
        Follow.objects.create(user=self.another_user,
                              author=self.user)
        self._test_subscr('posts:profile_unfollow')

    def test_post_after_sub(self):
        """ Проверка что вижу пост пользователя на которого подписался"""
        post = Post.objects.create(
            text='Тестовый текст',
            author=self.author,
            group=self.group
        )
        Follow.objects.create(user=self.another_user,
                              author=self.user)
        response = self.another_client.get(reverse('posts:follow_index'))
        post_text = post.text
        self.assertEqual(response.context['posts'].first().text, post_text)

    def test_post_after_unsub(self):
        """ Проверка что не вижу пост пользователя на которого подписался"""
        post = Post.objects.create(
            text='Тестовый текст',
            author=self.author,
            group=self.group
        )
        Follow.objects.create(user=self.another_user,
                              author=self.user)
        self._test_subscr('posts:profile_unfollow')
        response = self.another_client.get(reverse('posts:follow_index'))
        self.assertNotEqual(response.context['posts'].first(), post)
