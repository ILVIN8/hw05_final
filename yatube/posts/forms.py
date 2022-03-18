from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("group", "text", "image")
        labels = {
            "text": "Текст поста",
            "group": "Группа",
            "image": "Изображение",
        }
        help_texts = {
            "text": "Текст нового поста",
            "group": "Группа, к которой будет относиться пост",
            "image": "Загрузить изображение для поста",
        }

    def clean_text(self):
        data = self.cleaned_data["text"]
        if not data:
            raise forms.ValidationError("поле Text не должно быть пустым")

        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)
        labels = {
            "text": "Текст комментария",
        }
        help_texts = {
            "text": "Текст комментария",
        }

    def clean_text(self):
        data = self.cleaned_data["text"]
        if not data:
            raise forms.ValidationError("поле Text не должно быть пустым")

        return data
