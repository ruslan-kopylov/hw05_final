from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from http import HTTPStatus
from ..models import Post, Group


User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_pages_available(self):
        """Проверяем доступность страниц"""
        pages = (
            '/',
            '/about/author/',
            '/about/tech/'
        )
        for page in pages:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)


class PostsUrlsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.not_author = User.objects.create_user(username='not_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )
        cls.post_url = f'/posts/{cls.post.id}/'
        cls.post_edit_url = f'/posts/{cls.post.id}/edit/'
        cls.profile_url = f'/profile/{cls.post.author}/'
        cls.group_url = f'/group/{PostsUrlsTests.group.slug}/'

    def setUp(self):
        self.unauthorized_user = Client()
        self.post_author = Client()
        self.post_author.force_login(self.author)
        self.not_post_author = Client()
        self.not_post_author.force_login(self.not_author)

    def test_unauthorized_user(self):
        """Проверяем доступность страниц неавторизованному юзеру"""
        urls = [
            '/',
            PostsUrlsTests.group_url,
            PostsUrlsTests.profile_url,
            PostsUrlsTests.post_url,
        ]
        for adress in urls:
            with self.subTest(adress=adress):
                response = self.unauthorized_user.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_for_unauthorized_user(self):
        """Проверяем редирект для неавторизованного юзера"""
        urls = {
            PostsUrlsTests.post_edit_url: '/auth/login/?next=/posts/1/edit/',
            '/create/': '/auth/login/?next=/create/'
        }
        for adress, redirects in urls.items():
            with self.subTest(adress=adress):
                response = self.unauthorized_user.get(adress)
                self.assertRedirects(response, redirects)

    def test_authorized_user(self):
        """Проверяем доступность страниц автору"""
        urls = [
            PostsUrlsTests.post_edit_url,
            '/create/'
        ]
        for adress in urls:
            with self.subTest(adress=adress):
                response = self.post_author.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_for_not_author(self):
        """Проверяем редирект со страницы /edit/ если юзер не автор"""
        response = self.not_post_author.get(PostsUrlsTests.post_edit_url)
        self.assertRedirects(response, PostsUrlsTests.post_url)

    def test_unexisting_page(self):
        """Проверяем запрос несуществующей страницы"""
        url = '/unexisting_page/'
        response = self.unauthorized_user.get(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_url_templates(self):
        """Проверяем шаблоны"""
        templates = {
            '/': 'posts/index.html',
            PostsUrlsTests.group_url: 'posts/group_list.html',
            PostsUrlsTests.profile_url: 'posts/profile.html',
            PostsUrlsTests.post_url: 'posts/post_detail.html',
            PostsUrlsTests.post_edit_url: 'posts/create_post.html',
            '/create/': 'posts/create_post.html'
        }
        for adress, template in templates.items():
            with self.subTest(adress=adress):
                response = self.post_author.get(adress)
                self.assertTemplateUsed(response, template)
