# Generated by Django 2.2.5 on 2019-10-21 22:33

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
            name='Duel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('round', models.PositiveIntegerField()),
                ('num_matches', models.PositiveIntegerField()),
                ('state', models.CharField(choices=[('SCHEDULED', ''), ('RUNNING', ''), ('FAILED', ''), ('COMPLETED', '')], default='SCHEDULED', max_length=100)),
                ('started_at', models.DateTimeField(null=True)),
                ('ended_at', models.DateTimeField(null=True)),
                ('logs', models.FilePathField(null=True, path='/app/data/media/duel_logs/')),
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
            name='Submission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('revision', models.PositiveIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('zip_file', models.FileField(upload_to='submissions/', validators=[django.core.validators.FileExtensionValidator(['zip'])])),
                ('github_source', models.CharField(blank=True, max_length=200, validators=[django.core.validators.RegexValidator('^https://github.com/[^/]+/[^/]+/tree/[^/]+$')])),
                ('is_public', models.BooleanField()),
                ('state', models.CharField(choices=[('WAITING_BUILD', ''), ('BUILDING', ''), ('BUILD_FAILED', ''), ('WAITING_SMOKE_TEST', ''), ('TESTING', ''), ('FAILED_SMOKE_TEST', ''), ('READY', '')], default='WAITING_BUILD', max_length=100)),
                ('image_started_at', models.DateTimeField(null=True)),
                ('image_ended_at', models.DateTimeField(null=True)),
                ('image_error_msg', models.CharField(blank=True, max_length=200)),
                ('image_name', models.CharField(blank=True, max_length=200)),
                ('image_logs', models.FilePathField(null=True, path='/app/data/media/submission_image_logs/')),
                ('test_started_at', models.DateTimeField(null=True)),
                ('test_ended_at', models.DateTimeField(null=True)),
                ('test_error_msg', models.CharField(blank=True, max_length=200)),
                ('test_logs', models.FilePathField(null=True, path='/app/data/media/submission_test_logs/')),
                ('environment', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.Environment')),
                ('submitter', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Tournament',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('edition', models.PositiveIntegerField()),
                ('current_round', models.PositiveIntegerField()),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('state', models.CharField(choices=[('RUNNING', ''), ('FAILED', ''), ('COMPLETED', '')], default='RUNNING', max_length=100)),
                ('ended_at', models.DateTimeField(null=True)),
                ('environment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Environment')),
            ],
        ),
        migrations.CreateModel(
            name='TournamentSubmission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wins', models.PositiveIntegerField()),
                ('losses', models.PositiveIntegerField()),
                ('draws', models.PositiveIntegerField()),
                ('points', models.PositiveIntegerField()),
                ('total_score', models.FloatField()),
                ('ranking', models.PositiveIntegerField()),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Submission')),
                ('tournament', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Tournament')),
            ],
        ),
        migrations.AddField(
            model_name='tournament',
            name='submissions',
            field=models.ManyToManyField(through='core.TournamentSubmission', to='core.Submission'),
        ),
        migrations.CreateModel(
            name='DuelSubmission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('win', models.PositiveIntegerField()),
                ('loss', models.PositiveIntegerField()),
                ('draw', models.PositiveIntegerField()),
                ('score', models.FloatField()),
                ('duel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Duel')),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Submission')),
            ],
        ),
        migrations.AddField(
            model_name='duel',
            name='submissions',
            field=models.ManyToManyField(through='core.DuelSubmission', to='core.Submission'),
        ),
        migrations.AddField(
            model_name='duel',
            name='tournament',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Tournament'),
        ),
    ]