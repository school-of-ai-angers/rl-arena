# Generated by Django 2.2.5 on 2019-11-01 00:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20191027_1017'),
    ]

    operations = [
        migrations.AlterField(
            model_name='duel',
            name='logs',
            field=models.FileField(null=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='duel',
            name='results',
            field=models.FileField(null=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='revision',
            name='image_logs',
            field=models.FileField(null=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='revision',
            name='test_logs',
            field=models.FileField(null=True, upload_to=''),
        ),
    ]
