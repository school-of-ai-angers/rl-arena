# Setup logs
from django.apps import AppConfig
from core.settings import *
import django
import os
from yaml import safe_load


INSTALLED_APPS = [
    'core.apps.Config',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
]

# Start Django in stand-alone mode
print('Setup Django')
django.setup()

if __name__ == "__main__":
    from core.models import Environment
    # Create environments
    for env_entry in os.scandir('environments'):
        if env_entry.is_dir():
            info_path = os.path.join(env_entry.path, 'info.yml')
            if not os.path.exists(info_path):
                continue
            with open(info_path) as fp:
                env_dict = safe_load(fp)
            _, created = Environment.objects.update_or_create(
                slug=env_dict['slug'], defaults=env_dict)
            print(
                f'{env_dict["slug"]} - {"created" if created else "updated"}')
