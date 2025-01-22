from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import UserProfile, GitRepository
from .forms import CloudProviderForm, GitRepositoryForm

@login_required
def dashboard_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    context = {'profile': profile}
    return render(request, 'dashboard/index.html', context)

@login_required
def settings_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = CloudProviderForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('dashboard:dashboard')
    else:
        form = CloudProviderForm(instance=profile)
    return render(request, 'dashboard/settings.html', {'form': form})
@login_required
def git_repository_list(request):
    repositories = GitRepository.objects.filter(user=request.user)
    return render(request, 'dashboard/git_repository_list.html', {'repositories': repositories})

@login_required
def git_repository_create(request):
    if request.method == 'POST':
        form = GitRepositoryForm(request.POST)
        if form.is_valid():
            git_repo = form.save(commit=False)
            git_repo.user = request.user
            git_repo.save()
            return redirect('dashboard:git_repository_list')
    else:
        form = GitRepositoryForm()
    return render(request, 'dashboard/git_repository_create.html', {'form': form})


