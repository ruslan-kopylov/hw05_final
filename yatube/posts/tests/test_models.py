from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Comment, Group, Post

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
            text='Тестовый пост ' * 15,
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Тестовый комментарий',
            post=cls.post
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        expected_post_str = PostModelTest.post.text[:15]
        expected_group_str = PostModelTest.group.title
        expected_comment_str = PostModelTest.comment.text
        self.assertEqual(expected_post_str, str(PostModelTest.post))
        self.assertEqual(expected_group_str, str(PostModelTest.group))
        self.assertEqual(expected_comment_str, str(PostModelTest.comment))
