# Generated by Django 2.2.5 on 2019-10-20 12:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_load_fixtures'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='image_error_msg',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
