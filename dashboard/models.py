from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cloud_provider = models.CharField(
        max_length=10,
        choices=[
            ('aws', 'AWS'),
            ('gcp', 'GCP'),
            ('azure', 'Azure'),
        ],
        default='aws'
    )
    # AWS Keys
    aws_access_key = models.CharField(max_length=255, blank=True, null=True)
    aws_secret_key = models.CharField(max_length=255, blank=True, null=True)
    
    # GCP Key File Path
    gcp_key_file = models.FileField(upload_to='gcp_keys/', blank=True, null=True)
    
    # Azure Credentials
    azure_tenant_id = models.CharField(max_length=255, blank=True, null=True)
    azure_client_id = models.CharField(max_length=255, blank=True, null=True)
    azure_client_secret = models.CharField(max_length=255, blank=True, null=True)
    azure_subscription_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.cloud_provider}"

from django.db import models
from django.contrib.auth.models import User

class GitRepository(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='git_repositories')
    repo_url = models.TextField(null=True, blank=True)
    private_key = models.TextField(verbose_name="Приватний ключ")
    service_name = models.CharField(max_length=255, verbose_name="Назва сервісу", null=True, blank=True)  
    docker_image = models.CharField(max_length=255, verbose_name="Docker Image URI", null=True, blank=True)
    branch = models.CharField(max_length=100, verbose_name="Git Branch", default="main")
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.service_name} - {self.repo_url} - {self.user.username}"
