from http.client import OK
from http.client import NOT_FOUND
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.core.cache import cache

from ..models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый текст поста",
        )
        cls.post_edit_url = f"/posts/{cls.post.id}/edit/"
        cls.public_urls = (
            ("/", "posts/index.html"),
            (f"/group/{cls.group.slug}/", "posts/group_list.html"),
            (f"/profile/{cls.user.username}/", "posts/profile.html"),
            (f"/posts/{cls.post.id}/", "posts/post_detail.html"),
        )
        cls.private_urls = (
            ("/create/", "posts/create_post.html"),
            (cls.post_edit_url, "posts/create_post.html"),
        )
        cls.unexisting_urls = "/unexisting_page/"

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username="HasNoName")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_url_exists_at_desired_location(self):
        """Страница / доступна любому пользователю."""
        response = self.guest_client.get(self.public_urls[0][0])
        self.assertEqual(response.status_code, OK)

    def test_group_url_exists_at_desired_location(self):
        """Страница /group/test_slug/ доступна любому пользователю."""
        response = self.guest_client.get(self.public_urls[1][0])
        self.assertEqual(response.status_code, OK)

    def test_profile_url_exists_at_desired_location(self):
        """Страница /profile/auth/ доступна любому пользователю."""
        response = self.guest_client.get(self.public_urls[2][0])
        self.assertEqual(response.status_code, OK)

    def test_posts_url_exists_at_desired_location(self):
        """Страница /posts/1/ доступна любому пользователю."""
        response = self.guest_client.get(self.public_urls[3][0])
        self.assertEqual(response.status_code, OK)

    def test_404_url_exists_at_desired_location(self):
        """Страница /unexisting_page/
        возращает 404 ошибку любому пользователю."""
        response = self.guest_client.get(self.unexisting_urls)
        self.assertEqual(response.status_code, NOT_FOUND)

    def test_create_url_exists_at_desired_location(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get(self.private_urls[0][0])
        self.assertEqual(response.status_code, OK)

    def test_post_edit_url_exists_at_desired_location_authorized(self):
        """Страница /posts/1/edit/ доступна авторизованному автору поста
        пользователю."""
        response = self.authorized_client.get(self.private_urls[1][0])
        self.assertEqual(response.status_code, OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            self.public_urls,
            self.private_urls,
        }
        for i in templates_url_names:
            for address, template in i:
                with self.subTest(address=address):
                    response = self.authorized_client.get(address)
                    self.assertTemplateUsed(response, template)
