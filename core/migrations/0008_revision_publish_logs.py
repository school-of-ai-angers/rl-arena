# Generated by Django 2.2.5 on 2019-11-04 20:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_auto_20191101_2210'),
    ]

    operations = [
        migrations.AddField(
            model_name='revision',
            name='publish_logs',
            field=models.FileField(null=True, upload_to=''),
        ),
    ]