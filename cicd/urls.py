from django.urls import path
from . import views

app_name = 'cicd'

urlpatterns = [
    path('projects/', views.project_list, name='project_list'),
    path('projects/<int:repo_id>/', views.project_detail, name='project_detail'),
    path('create-helm-chart/', views.create_helm_chart, name='create_helm_chart'),
    path('git-repository-sync/<int:repo_id>/', views.git_repository_sync_view, name='git_repository_sync'),
]
