from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.template import loader
from .models import Environment, User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from .forms import CreateAccountForm

# Accounts


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


def user_home(request, username):
    user = get_object_or_404(User, username=username)
    return render(request, 'rl_arena/user_home.html', {
        'user': user
    })


def home(request):
    environments = Environment.objects.all()
    return render(request, 'rl_arena/home.html', {
        'environments': environments
    })


def environment_home(request, slug):
    environment = get_object_or_404(Environment, slug=slug)
    return render(request, 'rl_arena/environment_home.html', {
        'environment': environment
    })
