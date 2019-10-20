"""web URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
import django.contrib.auth.views as auth_views

import web.views as views

urlpatterns = [
    # Accounts
    path('login/', auth_views.LoginView.as_view(template_name='web/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('create_account/', views.create_account, name='create_account'),
    path('user/<username>/', views.user_home, name='user_home'),

    # Main app
    path('', views.home, name='home'),
    path('environment/<slug>/',
         views.environment_home, name='environment_home'),
    path('environment/<slug>/submission/new',
         views.new_submission, name='new_submission'),
    path('environment/<slug>/submission/<int:pk>',
         views.submission_home, name='submission_home'),
    path('environment/<slug>/submission/<int:pk>/download',
         views.submission_download, name='submission_download'),
    path('environment/<slug>/submission/<int:pk>/image_logs',
         views.submission_image_logs, name='submission_image_logs'),
    path('environment/<slug>/submission/<int:pk>/test_logs',
         views.submission_test_logs, name='submission_test_logs'),
]
