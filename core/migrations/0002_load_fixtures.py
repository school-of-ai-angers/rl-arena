# Generated by Django 2.2.5 on 2019-10-20 10:19

from django.db import migrations
import os
from yaml import safe_load
from django.contrib.auth.hashers import make_password


def load_fixtures(apps, schema_editor):
    # Create super user
    User = apps.get_model('core', 'User')
    User.objects.create(
        username=os.environ['SUPERUSER_USERNAME'],
        email=os.environ['SUPERUSER_EMAIL'],
        password=make_password(os.environ['SUPERUSER_PASSWORD']),
        is_superuser=True,
        is_staff=True
    )

    # Create environments
    Environment = apps.get_model('core', 'Environment')
    for env_entry in os.scandir('environments'):
        if env_entry.is_dir():
            with open(os.path.join(env_entry.path, 'info.yml')) as fp:
                env_dict = safe_load(fp)
            Environment.objects.create(**env_dict)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_fixtures)
    ]
