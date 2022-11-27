from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..forms import PostForm

from ..models import Group, Post


User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
        )
        cls.test_dict = {
            'text': cls.post.text[:15],
            'group_title': cls.group.title
        }
        cls.form = PostForm()

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        str_fields = {
            'text': self.post,
            'group_title': self.group
        }
        for key in str_fields:
            if key in str_fields:
                with self.subTest():
                    self.assertEqual(self.test_dict[key], str(str_fields[key]))

    def test_title_label(self):
        text_label = self.form.fields['text'].label
        self.assertEqual(text_label, 'Текст')
        group_label = self.form.fields['group'].label
        self.assertEqual(group_label, 'Группа')

    def test_title_help_text(self):
        group_help_text = self.form.fields['group'].help_text
        self.assertEqual(group_help_text, 'Выберите группу')
