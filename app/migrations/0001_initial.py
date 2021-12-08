# Generated by Django 3.2.9 on 2021-11-14 13:38

from django.db import migrations
from django.contrib.auth.models import User
from django.conf import settings


def generate_superuser(apps, schema_editor):
    User.objects.create_superuser(
        username=settings.DJANGO_SUPERUSER_USERNAME,
        email=settings.DJANGO_SUPERUSER_EMAIL,
        password=settings.DJANGO_SUPERUSER_PASSWORD,
        first_name=settings.DJANGO_SUPERUSER_FIRST_NAME,
        last_name=settings.DJANGO_SUPERUSER_LAST_NAME,
    )


class Migration(migrations.Migration):
    dependencies = []

    operations = [
        migrations.RunPython(generate_superuser),
    ]
