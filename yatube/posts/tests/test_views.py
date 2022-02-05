import shutil
import tempfile
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from ..models import Post, Group, Follow
from ..views import POSTS_PER_PAGE

NUMBER_OF_POSTS_COPIES = 15

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(
            username='author', first_name='Ruslan')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        for post_copy in range(5):
            Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост {post_copy}',
                group=cls.group
            )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded
        )
        cls.follower = User.objects.create_user(
            username='follower', first_name='Roman')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.post_author = Client()
        self.reader = Client()
        self.post_author.force_login(self.user)
        self.reader.force_login(self.follower)
        self.following = Follow.objects.create(
            user=self.follower,
            author=self.user
        )

    def test_authorized_user_following(self):
        """
        Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок.
        """
        self.reader.get(
            reverse(
                'posts:profile_follow',
                args=(self.user.username,)
            )
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.follower,
                author=self.user
            ).exists()
        )
        self.reader.get(
            reverse(
                'posts:profile_unfollow',
                args=(self.user.username,)
            )
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.follower,
                author=self.user
            ).exists()
        )

    def test_new_post_for_followers(self):
        """
        Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех,
        кто не подписан.
        """
        response = self.reader.get(reverse('posts:follow_index'))
        self.assertIn(
            self.post,
            response.context['page_obj']
        )
        self.following.delete()
        response = self.reader.get(reverse('posts:follow_index'))
        self.assertNotIn(
            self.post,
            response.context['page_obj']
        )

    def test_cache_index_page(self):
        """Проверяем работу кеширования index"""
        Post.objects.create(
            author=self.user,
            text='Тестирую кеш'
        )
        response = self.post_author.get(reverse('posts:index'))
        old_content = response.content
        self.assertEqual(response.context['page_obj'][0].text, 'Тестирую кеш')
        Post.objects.first().delete()
        response = self.post_author.get(reverse('posts:index'))
        self.assertEqual(response.content, old_content)
        cache.clear()
        response = self.post_author.get(reverse('posts:index'))
        self.assertNotEqual(
            response.content,
            old_content
        )

    def test_url_templates(self):
        """Проверяем шаблоны"""
        group_slug = PostsViewsTests.group.slug
        username = PostsViewsTests.user
        post_id = PostsViewsTests.post.pk
        templates = [
            ('posts/index.html', 'posts:index', None),
            ('posts/group_list.html', 'posts:group_post', (group_slug,)),
            ('posts/post_detail.html', 'posts:post_detail', (post_id,)),
            ('posts/profile.html', 'posts:profile', (username,)),
            ('posts/create_post.html', 'posts:post_create', None),
            ('posts/create_post.html', 'posts:post_edit', (post_id,))
        ]
        for template, adress, args in templates:
            with self.subTest(adress=adress):
                response = self.post_author.get(reverse(adress, args=args))
                self.assertTemplateUsed(response, template)

    def test_templates_show_correct_context(self):
        """
        Шаблоны index, profile, group list
        сформированы с правильным контекстом.
        """
        group_slug = PostsViewsTests.group.slug
        responses = [
            (
                'posts:index',
                None,
            ),
            (
                'posts:profile',
                (PostsViewsTests.user,),
            ),
            (
                'posts:group_post',
                (group_slug,),
            )
        ]
        for resp, args in responses:
            with self.subTest(resp=resp):
                response = self.post_author.get(reverse(resp, args=args))
                post_on_page = response.context['page_obj'][0]
                post_text = post_on_page.text
                post_group = post_on_page.group.title
                post_author = post_on_page.author.username
                post_image = post_on_page.image.name
                values = {
                    post_text: 'Тестовый пост',
                    post_group: 'Тестовая группа',
                    post_author: 'author',
                    post_image: PostsViewsTests.post.image
                }
                for key, value in values.items():
                    with self.subTest(key=key):
                        self.assertEqual(key, value)

    def test_template_post_detail_correct_context(self):
        """Шаблон post detail сформирован с правильным контекстом."""
        post_id = PostsViewsTests.post.pk
        response = self.post_author.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': post_id}
        )
        )
        values = {
            'post': PostsViewsTests.post,
            'posts_count': PostsViewsTests.post.author.posts.all().count()
        }
        for key, value in values.items():
            with self.subTest(key=key):
                self.assertEqual(response.context[key], value)
        self.assertEqual(
            response.context['post'].image.name,
            'posts/small.gif'
        )

    def test_template_create_post_correct_context(self):
        """Шаблон create post сформирован с правильным контекстом."""
        response = self.post_author.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_template_edit_post_correct_context(self):
        """Шаблон edit post сформирован с правильным контекстом."""
        post_id = PostsViewsTests.post.pk
        response = self.post_author.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': post_id}
        )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertEqual(response.context['post'], PostsViewsTests.post)

    def test_post_with_group(self):
        """Пост с группой попадает на нужные страницы"""
        second_group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug_2',
            description='Тестовое описание 2',
        )
        addresses = [
            ('posts:index', None, True),
            ('posts:profile', (PostsViewsTests.user,), True),
            ('posts:group_post', (PostsViewsTests.group.slug,), True),
            ('posts:group_post', (second_group.slug,), False)
        ]
        for address, args, result in addresses:
            with self.subTest(address=address):
                response = self.post_author.get(reverse(address, args=args))
                self.assertEqual(
                    PostsViewsTests.post in response.context['page_obj'],
                    result)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        for post_copy in range(NUMBER_OF_POSTS_COPIES):
            Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост {post_copy}',
                group=cls.group
            )

    def setUp(self):
        self.post_author = Client()
        self.post_author.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        """Проверка: количество постов на первой странице равно 10"""
        response = self.post_author.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), POSTS_PER_PAGE)

    def test_second_pages_contains_five_records(self):
        """Проверка: на вторых страницах должно быть по пять постов."""
        group_slug = PaginatorViewsTest.group.slug
        username = PaginatorViewsTest.user
        number_of_posts = NUMBER_OF_POSTS_COPIES - POSTS_PER_PAGE
        response = self.post_author.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), number_of_posts)
        values = [
            reverse('posts:index'),
            reverse(
                'posts:group_post',
                kwargs={'slug': group_slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': username}
            )
        ]
        for value in values:
            with self.subTest(value=value):
                response = self.post_author.get(value + '?page=2')
                self.assertEqual(len(
                    response.context['page_obj']),
                    number_of_posts)
