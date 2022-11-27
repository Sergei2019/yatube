from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls.base import reverse
from http import HTTPStatus

from ..models import Group, Post


User = get_user_model()

OK = HTTPStatus.OK
FOUND = HTTPStatus.FOUND


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=User.objects.create_user(username='Sergei'),
            group=Group.objects.create(slug='test-group')
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.get(username='Sergei')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.another_client = Client()
        self.user2 = User.objects.create_user(username='SobolevS')
        self.another_client.force_login(self.user2)

    def test_page_exists_at_desired_location(self):
        url_names = {reverse('posts:group_list',
                             kwargs={'slug': self.post.group.slug}): OK,
                     reverse('posts:profile',
                             kwargs={'username':
                                     self.post.author.username}): OK,
                     reverse('posts:post_detail',
                             kwargs={'post_id': self.post.id}): OK,
                     '/posts/unexist/': HTTPStatus.NOT_FOUND,
                     reverse('about:author'): OK,
                     reverse('about:tech'): OK,
                     reverse('posts:index'): OK,
                     reverse('posts:add_comment',
                             kwargs={'post_id': self.post.id}): FOUND,
                     reverse('posts:follow_index'): FOUND,
                     reverse('posts:profile_follow',
                             kwargs={'username':
                                     self.post.author.username}): FOUND,
                     reverse('posts:profile_unfollow',
                             kwargs={'username':
                                     self.post.author.username}): FOUND
                     }
        for adress, status in url_names.items():
            with self.subTest():
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, status)

    def test_create_post_url_exists_at_desired_location(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post_url_exists_at_desired_location_author(self):
        """Страница /post/post_id/edit для автора поста."""
        response = (self.authorized_client.
                    get(reverse('posts:post_edit',
                                kwargs={'post_id': self.post.id})))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post_url_exists_at_desired_location_authorized(self):
        """Страница /post/post_id/edit для не автора поста."""
        response = (self.another_client.
                    get(reverse('posts:post_edit',
                                kwargs={'post_id': self.post.id})))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.post.group.slug}
                    ): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.post.author.username}
                    ): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}
                    ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}): 'posts/create_post.html'
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress, template=template):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)
