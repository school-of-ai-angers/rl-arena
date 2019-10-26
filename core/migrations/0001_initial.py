# Generated by Django 2.2.5 on 2019-10-26 14:35

import core.models
from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('email', models.EmailField(help_text='Your email address will not be made public and will not be used for communications. It will only be used as your authentication identifier.', max_length=254, unique=True)),
                ('github', models.CharField(blank=True, help_text='Your GitHub username if you have one and want to link to it', max_length=100, validators=[django.contrib.auth.validators.UnicodeUsernameValidator])),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Competitor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_public', models.BooleanField()),
                ('name', models.SlugField()),
                ('last_version', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Environment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(unique=True)),
                ('description', models.TextField()),
                ('num_matches_in_duel', models.PositiveIntegerField()),
                ('memory_limit', models.CharField(max_length=50)),
                ('cpu_limit', models.FloatField()),
                ('image', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Revision',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version_number', models.PositiveIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('zip_file', models.FileField(upload_to=core.models.zip_file_path, validators=[django.core.validators.FileExtensionValidator(['zip'])])),
                ('publish_state', models.CharField(choices=[('PUBLISH_SKIPPED', ''), ('PUBLISH_SCHEDULED', ''), ('PUBLISH_RUNNING', ''), ('PUBLISH_FAILED', ''), ('PUBLISH_COMPLETED', '')], max_length=100)),
                ('publish_started_at', models.DateTimeField(null=True)),
                ('publish_ended_at', models.DateTimeField(null=True)),
                ('publish_error_msg', models.CharField(blank=True, max_length=200)),
                ('publish_url', models.CharField(blank=True, max_length=200, validators=[django.core.validators.RegexValidator('^https://github.com/')])),
                ('image_state', models.CharField(choices=[('IMAGE_SCHEDULED', ''), ('IMAGE_RUNNING', ''), ('IMAGE_FAILED', ''), ('IMAGE_COMPLETED', '')], default='IMAGE_SCHEDULED', max_length=100)),
                ('image_started_at', models.DateTimeField(null=True)),
                ('image_ended_at', models.DateTimeField(null=True)),
                ('image_error_msg', models.CharField(blank=True, max_length=200)),
                ('image_name', models.CharField(blank=True, max_length=200)),
                ('image_logs', models.FilePathField(null=True, path='/app/data/media/revision_image_logs/')),
                ('test_state', models.CharField(choices=[('TEST_SCHEDULED', ''), ('TEST_RUNNING', ''), ('TEST_FAILED', ''), ('TEST_COMPLETED', '')], default='TEST_SCHEDULED', max_length=100)),
                ('test_started_at', models.DateTimeField(null=True)),
                ('test_ended_at', models.DateTimeField(null=True)),
                ('test_error_msg', models.CharField(blank=True, max_length=200)),
                ('test_logs', models.FilePathField(null=True, path='/app/data/media/revision_test_logs/')),
                ('competitor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.Competitor')),
            ],
        ),
        migrations.CreateModel(
            name='Tournament',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('edition', models.PositiveIntegerField()),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('state', models.CharField(choices=[('RUNNING', ''), ('FAILED', ''), ('COMPLETED', '')], default='RUNNING', max_length=100)),
                ('ended_at', models.DateTimeField(null=True)),
                ('environment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Environment')),
            ],
        ),
        migrations.CreateModel(
            name='TournamentParticipant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wins', models.PositiveIntegerField()),
                ('losses', models.PositiveIntegerField()),
                ('draws', models.PositiveIntegerField()),
                ('points', models.PositiveIntegerField()),
                ('total_score', models.FloatField()),
                ('ranking', models.PositiveIntegerField()),
                ('revision', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Revision')),
                ('tournament', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Tournament')),
            ],
        ),
        migrations.AddField(
            model_name='tournament',
            name='participants',
            field=models.ManyToManyField(through='core.TournamentParticipant', to='core.Revision'),
        ),
        migrations.CreateModel(
            name='Duel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.CharField(choices=[('SCHEDULED', ''), ('RUNNING', ''), ('FAILED', ''), ('COMPLETED', '')], default='SCHEDULED', max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('started_at', models.DateTimeField(null=True)),
                ('ended_at', models.DateTimeField(null=True)),
                ('logs', models.FilePathField(null=True, path='/app/data/media/duel_logs/')),
                ('results', models.FilePathField(null=True, path='/app/data/media/duel_results/')),
                ('result', models.CharField(blank=True, choices=[('ERROR', ''), ('PLAYER_1_WIN', ''), ('PLAYER_2_WIN', ''), ('DRAW', '')], max_length=100)),
                ('error_msg', models.CharField(blank=True, max_length=200)),
                ('num_matches', models.PositiveIntegerField(null=True)),
                ('player_1_errors', models.PositiveIntegerField(null=True)),
                ('player_2_errors', models.PositiveIntegerField(null=True)),
                ('other_errors', models.PositiveIntegerField(null=True)),
                ('player_1_wins', models.PositiveIntegerField(null=True)),
                ('player_2_wins', models.PositiveIntegerField(null=True)),
                ('draws', models.PositiveIntegerField(null=True)),
                ('player_1_score', models.FloatField(null=True)),
                ('player_2_score', models.FloatField(null=True)),
                ('player_1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='player_1', to='core.Revision')),
                ('player_2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='player_2', to='core.Revision')),
                ('tournament', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Tournament')),
            ],
        ),
        migrations.AddField(
            model_name='competitor',
            name='environment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Environment'),
        ),
        migrations.AddField(
            model_name='competitor',
            name='submitter',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddConstraint(
            model_name='revision',
            constraint=models.UniqueConstraint(fields=('competitor', 'version_number'), name='unique_competitor'),
        ),
        migrations.AddConstraint(
            model_name='competitor',
            constraint=models.UniqueConstraint(fields=('environment', 'name'), name='unique_environment'),
        ),
    ]
