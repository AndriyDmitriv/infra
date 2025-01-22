from django import forms
from .models import UserProfile, GitRepository
import re

class CloudProviderForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'cloud_provider',
            'aws_access_key', 'aws_secret_key',
            'gcp_key_file',
            'azure_tenant_id', 'azure_client_id', 'azure_client_secret', 'azure_subscription_id'
        ]
        widgets = {
            'cloud_provider': forms.Select(attrs={'class': 'form-control'}),
            'aws_access_key': forms.TextInput(attrs={'class': 'form-control'}),
            'aws_secret_key': forms.PasswordInput(attrs={'class': 'form-control'}),
            'gcp_key_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'azure_tenant_id': forms.TextInput(attrs={'class': 'form-control'}),
            'azure_client_id': forms.TextInput(attrs={'class': 'form-control'}),
            'azure_client_secret': forms.PasswordInput(attrs={'class': 'form-control'}),
            'azure_subscription_id': forms.TextInput(attrs={'class': 'form-control'}),
        }


class GitRepositoryForm(forms.ModelForm):
    class Meta:
        model = GitRepository
        fields = ['repo_url', 'private_key', 'docker_image', 'branch']
        widgets = {
            'private_key': forms.Textarea(attrs={'rows': 5}),
        }
        labels = {
            'repo_url': 'URL репозиторію',
            'private_key': 'Приватний ключ',
            'docker_image': 'URI Docker Image',
            'branch': 'Гілка Git',
        }
