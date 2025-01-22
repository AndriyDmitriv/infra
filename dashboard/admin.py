from django.contrib import admin
from .models import UserProfile, GitRepository
# Register your models here.
admin.site.register(UserProfile)
admin.site.register(GitRepository)