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
    path('profile/', views.profile, name='profile'),


    # Main app
    path('', views.home, name='home'),
    path('environment/<env>/',
         views.environment_home, name='environment_home'),
    path('environment/<env>/competitor/<competitor>',
         views.competitor_home, name='competitor_home'),
    path('environment/<env>/tournament/<int:tournament>',
         views.environment_home, name='environment_home_with_tournament'),
    path('environment/<env>/tournament/<int:tournament>/competitor/<competitor>',
         views.tournament_participant, name='tournament_participant'),
    path('environment/<environment>/tournament/<int:tournament>/duel/<competitor_1>/<competitor_2>',
         views.duel_home, name='duel_home'),
    path('environment/<environment>/tournament/<int:tournament>/duel/<competitor_1>/<competitor_2>/<int:match>',
         views.duel_home, name='match_home'),

    # File downloads
    path('environment/<env>/competitor/<competitor>/revision/<int:revision>/download',
         views.revision_source_download, name='revision_source_download'),
    path('environment/<env>/competitor/<competitor>/revision/<int:revision>/image_logs',
         views.revision_image_logs_download, name='revision_image_logs_download'),
    path('environment/<env>/competitor/<competitor>/revision/<int:revision>/test_logs/<log_type>',
         views.revision_test_logs_download, name='revision_test_logs_download'),
    path('duel/<int:duel_id>/logs',
         views.duel_logs_download, name='duel_logs_download'),
    path('duel/<int:duel_id>/results',
         views.duel_results_download, name='duel_results_download'),
]
