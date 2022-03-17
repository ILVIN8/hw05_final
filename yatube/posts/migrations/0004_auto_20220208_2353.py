# Generated by Django 2.2.9 on 2022-02-08 20:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("posts", "0003_auto_20220208_0256"),
    ]

    operations = [
        migrations.AlterField(
            model_name="group",
            name="slug",
            field=models.SlugField(max_length=200, unique=True),
        ),
        migrations.AlterField(
            model_name="post",
            name="group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="posts.Group",
            ),
        ),
    ]