from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.template import loader
from .models import Environment
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from .forms import CreateAccountForm


def home(request):
    environments = Environment.objects.all()
    return render(request, 'rl_arena/home.html', {
        'environments': environments
    })


def create_account(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = CreateAccountForm(request.POST)
        if form.is_valid():
            form.save()
            email = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(email=email, password=raw_password)
            login(request, user)
            return redirect('home')
    else:
        form = CreateAccountForm()

    return render(request, 'rl_arena/create_account.html', {
        'form': form
    })


def environment_home(request, slug):
    return HttpResponse(f'The home page for the environment {slug}')
