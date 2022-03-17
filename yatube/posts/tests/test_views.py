import shutil
import tempfile
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.core.cache import cache

from ..models import Post, Group

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание группы",
        )
        cls.group_2 = Group.objects.create(
            title="Тестовая группа 2",
            slug="test-slug-2",
            description="Тестовое описание группы 2",
        )
        cls.posts = []
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        for i in range(13):
            cls.posts.append(
                Post.objects.create(
                    author=cls.user,
                    text=f"Тестовый текст поста {i}",
                    group=cls.group,
                    image=SimpleUploadedFile(
                        name=f"small_{i}.gif",
                        content=small_gif,
                        content_type="image/gif",
                    ),
                )
            )
        cls.post_2 = Post.objects.create(
            author=cls.user,
            text="Тестовый текст уникального поста",
            group=cls.group,
            image=SimpleUploadedFile(
                name="small_uniq.gif",
                content=small_gif,
                content_type="image/gif",
            ),
        )
        cls.post = Post.objects.get(id=1)
        cls.index_url = (reverse("posts:index"), "posts/index.html")
        cls.group_url = (
            reverse("posts:group_list", kwargs={"slug": cls.group.slug}),
            "posts/group_list.html",
        )
        cls.group_url_2 = (
            reverse("posts:group_list", kwargs={"slug": cls.group_2.slug}),
            "posts/group_list.html",
        )
        cls.profile_url = (
            reverse("posts:profile", kwargs={"username": cls.user.username}),
            "posts/profile.html",
        )
        cls.post_url = (
            reverse("posts:post_detail", kwargs={"post_id": cls.post.id}),
            "posts/post_detail.html",
        )
        cls.new_post_url = (
            reverse("posts:post_create"),
            "posts/create_post.html",
        )
        cls.edit_post_url = (
            reverse("posts:post_edit", kwargs={"post_id": cls.post.id}),
            "posts/create_post.html",
        )
        cls.follow_index_url = (
            reverse("posts:follow_index"),
            "posts/follow.html",
        )
        cls.follow_url = (
            reverse(
                "posts:profile_follow", kwargs={"username": cls.user.username}
            ),
            "posts/profile.html",
        )
        cls.unfollow_url = (
            reverse(
                "posts:profile_unfollow",
                kwargs={"username": cls.user.username},
            ),
            "posts/profile.html",
        )
        cls.paginated_urls = (cls.index_url, cls.group_url, cls.profile_url)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.user_2 = User.objects.create_user(username="Follower")
        self.follow_client = Client()
        self.follow_client.force_login(self.user_2)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            self.index_url,
            self.profile_url,
            self.post_url,
            self.new_post_url,
            self.edit_post_url,
            self.group_url,
        }
        for i in templates_pages_names:
            with self.subTest(reverse_name=i[0]):
                response = self.authorized_client.get(i[0])
                self.assertTemplateUsed(response, i[1])

    def test_first_page_contains_ten_records(self):
        response = self.client.get(self.paginated_urls[0][0])
        self.assertEqual(len(response.context["page_obj"]), 10)

    def test_second_page_contains_three_records(self):
        response = self.client.get(self.paginated_urls[0][0] + "?page=2")
        self.assertEqual(len(response.context["page_obj"]), 4)

    def test_first_group_list_page_contains_ten_records(self):
        response = self.client.get(self.paginated_urls[1][0])
        self.assertEqual(len(response.context["page_obj"]), 10)

    def test_second_group_list_page_contains_three_records(self):
        response = self.client.get(self.paginated_urls[1][0] + "?page=2")
        self.assertEqual(len(response.context["page_obj"]), 4)

    def test_first_profile_list_page_contains_ten_records(self):
        response = self.client.get(self.paginated_urls[2][0])
        self.assertEqual(len(response.context["page_obj"]), 10)

    def test_second_profile_list_page_contains_three_records(self):
        response = self.client.get(self.paginated_urls[2][0] + "?page=2")
        self.assertEqual(len(response.context["page_obj"]), 4)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.post_url[0])
        first_object = response.context["post"]
        post_text = first_object.text
        post_group_title = first_object.group.title
        post_author_username = first_object.author.username
        self.assertEqual(post_text, "Тестовый текст поста 0")
        self.assertEqual(post_group_title, "Тестовая группа")
        self.assertEqual(post_author_username, "auth")

    def test_existing_post_some_pages(self):
        tests_pages = {
            self.index_url,
            self.group_url,
            self.profile_url,
            self.group_url_2,
        }
        for i in tests_pages:
            with self.subTest(page=i[0]):
                response = self.authorized_client.get(i[0])
                result = False
                for post in response.context["page_obj"]:
                    post_text = post.text
                    post_group_title = post.group.title
                    post_author_username = post.author.username
                    if (
                        post_text == "Тестовый текст поста 12"
                        and post_group_title == "Тестовая группа"
                        and post_author_username == "auth"
                    ):
                        result = True
                        break
                if post_group_title == "Тестовая группа 2":
                    self.assertFalse(result)
                else:
                    self.assertTrue(result)

    def test_edit_post_page_show_correct_context(self):
        """Шаблон /edit_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.edit_post_url[0])
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_page_show_correct_context(self):
        """Шаблон /create сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.new_post_url[0])
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_image_correct_in_context(self):
        """Шаблоны главной, профайла, группы и поста
        сформированы с картинкой в контексте."""
        tests_pages = {
            self.index_url,
            self.group_url,
            self.profile_url,
        }
        for k in tests_pages:
            response = self.authorized_client.get(k[0])
            test_object = response.context["page_obj"][0]
            post_text = test_object.text
            post_group_title = test_object.group.title
            post_author_username = test_object.author.username
            post_image = test_object.image
            self.assertEqual(post_text, "Тестовый текст уникального поста")
            self.assertEqual(post_group_title, "Тестовая группа")
            self.assertEqual(post_author_username, "auth")
            self.assertEqual(post_image, "posts/small_uniq.gif")

    def test_image_correct_in_context_in_post_detail(self):
        """Шаблон страницы поста сформирован с картинкой в контексте."""
        tests_pages = {
            self.post_url,
        }
        for k in tests_pages:
            response = self.authorized_client.get(k[0])
            test_object = response.context["post"]
            post_text = test_object.text
            post_group_title = test_object.group.title
            post_author_username = test_object.author.username
            post_image = test_object.image
            self.assertEqual(post_text, "Тестовый текст поста 0")
            self.assertEqual(post_group_title, "Тестовая группа")
            self.assertEqual(post_author_username, "auth")
            self.assertEqual(post_image, "posts/small_0.gif")

    def test_cache_post(self):
        """Проверка корректной работы кэширования постов"""
        response_1 = self.authorized_client.get(self.index_url[0])
        result_1 = response_1.content
        Post.objects.get(id=1).delete()
        response_2 = self.authorized_client.get(self.index_url[0])
        result_2 = response_2.content
        self.assertTrue(result_1 == result_2)
        cache.clear()
        response_3 = self.authorized_client.get(self.index_url[0])
        result_3 = response_3.content
        self.assertFalse(result_1 != result_3)

    def test_follow_unfollow(self):
        """Проверка корректной работы фоллоу и анфоллоу"""
        response_followed = self.follow_client.get(
            reverse("posts:follow_index")
        )
        self.assertEqual(len(response_followed.context["page_obj"]), 0)
        self.follow_client.get(
            reverse(
                "posts:profile_follow", kwargs={"username": self.user.username}
            )
        )
        response_followed = self.follow_client.get(
            reverse("posts:follow_index")
        )
        self.assertEqual(len(response_followed.context["page_obj"]), 10)
        self.follow_client.get(
            reverse(
                "posts:profile_unfollow",
                kwargs={"username": self.user.username},
            )
        )
        response_followed = self.follow_client.get(
            reverse("posts:follow_index")
        )
        self.assertEqual(len(response_followed.context["page_obj"]), 0)

    def test_follow_index_page(self):
        """Проверка корректной работы ленты фолловера
        и обычного пользователя"""
        response_followed = self.follow_client.get(
            reverse("posts:follow_index")
        )
        self.assertEqual(len(response_followed.context["page_obj"]), 0)
        self.follow_client.get(
            reverse(
                "posts:profile_follow", kwargs={"username": self.user.username}
            )
        )
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        self.post_3 = Post.objects.create(
            author=self.user,
            text="Тестовое обращение автора к подписчикам",
            group=self.group,
            image=SimpleUploadedFile(
                name="small_uni_3.gif",
                content=small_gif,
                content_type="image/gif",
            ),
        )

        response = self.follow_client.get(reverse("posts:follow_index")[0])
        test_object = response.context["page_obj"][0]
        post_text = test_object.text
        post_group_title = test_object.group.title
        post_author_username = test_object.author.username
        post_image = test_object.image
        self.assertEqual(post_text, "Тестовое обращение автора к подписчикам")
        self.assertEqual(post_group_title, "Тестовая группа")
        self.assertEqual(post_author_username, "auth")
        self.assertEqual(post_image, "posts/small_uni_3.gif")
        response_another_follower = self.authorized_client.get(
            reverse("posts:follow_index")
        )
        self.assertEqual(len(response_another_follower.context["page_obj"]), 0)
