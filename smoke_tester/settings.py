"""
Django settings for rl_arena project.

Generated by 'django-admin startproject' using Django 2.2.5.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

from core.settings import *

INSTALLED_APPS = [
    'core.apps.Config',
    'smoke_tester.apps.Config',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
]
