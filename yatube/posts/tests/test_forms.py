import shutil
import tempfile
from django.contrib.auth import get_user_model
from ..forms import PostForm
from ..models import Post, Comment
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост содержащий очень большое количество букв",
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_not_create_post(self):
        """Неавторизованный пользователь не может создать запись Post."""
        posts_count = Post.objects.count()
        form_data = {
            "text": "Тестовый текст, который не будет опубликован",
        }
        response = self.guest_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        self.assertRedirects(
            response,
            f'{reverse("users:login")}?next={reverse("posts:post_create")}',
            status_code=302,
        )
        self.assertEqual(Post.objects.count(), posts_count)

    def test_create_post(self):
        """Валидная форма создает запись Post."""
        posts_count = Post.objects.count()
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        uploaded = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )
        form_data = {
            "text": "Тестовый текст",
            "image": uploaded,
        }
        response = self.authorized_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        self.assertRedirects(
            response, reverse("posts:profile", kwargs={"username": "auth"})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        author = User.objects.get(username="auth")
        self.assertTrue(
            Post.objects.filter(
                author=author,
                text="Тестовый текст",
                image="posts/small.gif",
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма редактирует запись Post."""
        posts_count = Post.objects.count()
        form_data = {
            "text": "Тестовый отредактированный текст",
        }
        response = self.authorized_client.post(
            reverse("posts:post_edit", args=("1",)),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse("posts:post_detail", kwargs={"post_id": 1})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        author = User.objects.get(username="auth")
        self.assertTrue(
            Post.objects.filter(
                author=author,
                text="Тестовый отредактированный текст",
            ).exists()
        )

    def test_not_create_comment(self):
        """Неавторизованный пользователь не может комментировать пост."""
        comment_count = Comment.objects.count()
        form_data = {
            "text": "Тестовый комментарий, который не будет опубликован",
        }
        response = self.guest_client.post(
            reverse("posts:add_comment", kwargs={"post_id": 1}),
            data=form_data,
            follow=True,
        )
        login_url = reverse("users:login")
        add_comment_url = reverse("posts:add_comment", kwargs={"post_id": 1})
        self.assertRedirects(
            response,
            f"{login_url}?next={add_comment_url}",
            status_code=302,
        )
        self.assertEqual(Comment.objects.count(), comment_count)

    def test_create_comment(self):
        """Авторизованный пользователь успешно комментирует пост."""
        comment_count = Comment.objects.count()
        form_data = {
            "text": "Тестовый комментарий",
            "author": self.user,
        }
        response = self.authorized_client.post(
            reverse("posts:add_comment", kwargs={"post_id": 1}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse("posts:post_detail", kwargs={"post_id": 1})
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        author = User.objects.get(username="auth")
        self.assertTrue(
            Comment.objects.filter(
                author=author,
                text="Тестовый комментарий",
            ).exists()
        )
