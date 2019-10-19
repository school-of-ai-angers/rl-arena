from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from .models import Environment


def home(request):
    environments = Environment.objects.all()
    template = loader.get_template('rl_arena/home.html')
    return HttpResponse(template.render({
        'environments': environments
    }, request))


def environment_home(request, slug):
    return HttpResponse(f'The home page for the environment {slug}')
