from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('settings/', views.settings_view, name='settings'),
    path('git-repositories/', views.git_repository_list, name='git_repository_list'),
    path('git-repositories/create/', views.git_repository_create, name='git_repository_create'),
]