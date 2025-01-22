import os
from django.shortcuts import render
from django.http import HttpResponse
from .forms import HelmChartForm, GitSyncForm
import shutil
from dashboard.models import GitRepository
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import git
import subprocess
import yaml

def create_helm_chart(request):
    if request.method == "POST":
        form = HelmChartForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            # Збираємо ConfigMap
            config_map_keys = request.POST.getlist("config_map_keys")
            config_map_values = request.POST.getlist("config_map_values")
            config_map = dict(zip(config_map_keys, config_map_values))

            # Структура для Helm-чарту
            chart_name = data["app_name"]
            chart_dir = os.path.join(os.path.dirname(__file__), "generated_charts", chart_name)
            templates_dir = os.path.join(chart_dir, "templates")

            # Створюємо необхідні папки
            os.makedirs(templates_dir, exist_ok=True)

            # Створюємо Chart.yaml
            chart_yaml_content = f"""
apiVersion: v2
name: {chart_name}
description: A Helm chart for Kubernetes
version: 1.0.0
appVersion: "1.0.0"
"""
            with open(os.path.join(chart_dir, "Chart.yaml"), "w") as chart_file:
                chart_file.write(chart_yaml_content)

            # Створюємо prod-values.yaml
            values_yaml_content = f"""
replicaCount: {data['replica_count']}
image:
  repository: {data['image_repository']}
  tag: {data['image_tag']}
service:
  type: {data['service_type']}
  port: {data['service_port']}
  targetPort: {data['target_port']}
hpa:
  enabled: {data['hpa_enabled']}
  minReplicas: {data.get('hpa_min_replicas', 1)}
  maxReplicas: {data.get('hpa_max_replicas', 5)}
  targetCPUUtilizationPercentage: {data.get('hpa_target_cpu', 80)}
configMap:
{chr(10).join([f"  {key}: {value}" for key, value in config_map.items()])}
"""
            with open(os.path.join(chart_dir, "prod-values.yaml"), "w") as values_file:
                values_file.write(values_yaml_content)

            # Копіюємо шаблони
            source_helm_dir = os.path.join(os.path.dirname(__file__), "helm")
            for file_name in os.listdir(source_helm_dir):
                full_file_path = os.path.join(source_helm_dir, file_name)
                if os.path.isfile(full_file_path):
                    shutil.copy(full_file_path, templates_dir)

            return HttpResponse(f"Helm-чарт для {chart_name} успішно створено у {chart_dir}!")
    else:
        form = HelmChartForm()

    return render(request, "cicd/create_helm_chart.html", {"form": form})







@login_required
def git_repository_sync_view(request, repo_id):
    git_repo = get_object_or_404(GitRepository, id=repo_id, user=request.user)
    message = None
    success = False

    if request.method == "POST":
        form = GitSyncForm(request.POST)
        if form.is_valid():
            branch_name = form.cleaned_data['branch_name']

            # Шляхи
            base_dir = os.path.dirname(os.path.abspath(__file__))
            temp_dir = os.path.join(base_dir, "temp")
            os.makedirs(temp_dir, exist_ok=True)

            clone_dir = os.path.join(temp_dir, f"repo_{repo_id}")
            helm_chart_dir = os.path.join(base_dir, "generated_charts")
            if os.path.exists(clone_dir):
                shutil.rmtree(clone_dir)

            key_file_path = os.path.join(temp_dir, f"id_rsa_{repo_id}")
            try:
                # Створення ключа
                with open(key_file_path, "w") as key_file:
                    key_file.write(git_repo.private_key)
                os.chmod(key_file_path, 0o600)

                if not os.path.exists(key_file_path):
                    message = f"Key file {key_file_path} was not created."
                else:
                    # Клонування репозиторію
                    os.environ["GIT_SSH_COMMAND"] = f"ssh -i {key_file_path} -o StrictHostKeyChecking=no"
                    clone_cmd = f"git clone {git_repo.repo_url} {clone_dir}"
                    clone_result = subprocess.run(
                        clone_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                    )

                    if clone_result.returncode != 0:
                        message = f"Git clone failed. Error: {clone_result.stderr}"
                    else:
                        # Генеруємо CI/CD файл
                        ci_cd_path = os.path.join(clone_dir, ".github", "workflows")
                        os.makedirs(ci_cd_path, exist_ok=True)
                        pipeline_content = generate_ci_cd_pipeline(git_repo, helm_chart_dir)
                        with open(os.path.join(ci_cd_path, "ci-cd.yml"), "w") as pipeline_file:
                            pipeline_file.write(pipeline_content)

                        # Копіюємо Helm-чарт у репозиторій
                        repo_helm_dir = os.path.join(clone_dir, "helm")
                        if os.path.exists(repo_helm_dir):
                            shutil.rmtree(repo_helm_dir)
                        shutil.copytree(helm_chart_dir, repo_helm_dir)

                        # Додаємо зміни, комітимо та пушимо
                        repo = git.Repo(clone_dir)
                        repo.git.add(all=True)
                        repo.git.commit("-m", f"Add CI/CD pipeline and Helm charts for branch {branch_name}")
                        repo.git.push("origin", branch_name)

                        success = True
                        message = f"CI/CD pipeline and Helm charts synced successfully to branch {branch_name}."

                # Видаляємо ключ
                if os.path.exists(key_file_path):
                    os.remove(key_file_path)

            except Exception as e:
                message = str(e)
                if os.path.exists(key_file_path):
                    os.remove(key_file_path)

    else:
        form = GitSyncForm()
    return render(request, 'cicd/git_repository_sync.html', {'form': form, 'message': message, 'success': success})


@login_required
def project_list(request):
    projects = GitRepository.objects.filter(user=request.user)
    return render(request, 'cicd/project_list.html', {'projects': projects})

@login_required
def project_detail(request, repo_id):
    project = get_object_or_404(GitRepository, id=repo_id, user=request.user)
    helm_form = HelmChartForm()
    git_form = GitSyncForm()

    return render(request, 'cicd/project_detail.html', {
        'project': project,
        'helm_form': helm_form,
        'git_form': git_form,
    })


def generate_ci_cd_pipeline(repo, helm_chart_dir):
    pipeline = {
        'name': 'CI/CD',
        'on': {
            'push': {
                'branches': [repo.branch]
            }
        },
        'jobs': {
            'build-and-push': {
                'runs-on': 'self-hosted',
                'steps': [
                    {'name': 'Checkout Code', 'uses': 'actions/checkout@v2'},
                    {
                        'name': 'Set up Google Cloud',
                        'uses': 'google-github-actions/auth@v2',
                        'with': {
                            'credentials_json': '${{ secrets.GCP_CREDENTIALS }}'
                        }
                    },
                    {
                        'name': 'Configure Docker',
                        'run': f'gcloud auth configure-docker us-east4-docker.pkg.dev --quiet'
                    },
                    {
                        'name': 'Set short git commit SHA',
                        'id': 'vars',
                        'run': (
                            'calculatedSha=$(git rev-parse --short ${{ github.sha }})\n'
                            'echo "COMMIT_SHORT_SHA=$calculatedSha" >> $GITHUB_ENV'
                        )
                    },
                    {
                        'name': 'Build and Push Docker Image',
                        'env': {
                            'COMMIT_SHA': '${{ github.sha }}',
                            'IMAGE_URI': repo.docker_image
                        },
                        'run': (
                            'docker build --no-cache -t ${{ env.IMAGE_URI }}:${{ env.COMMIT_SHORT_SHA }} .\n'
                            'docker push ${{ env.IMAGE_URI }}:${{ env.COMMIT_SHORT_SHA }}\n'
                            'docker rmi  ${{ env.IMAGE_URI }}:${{ env.COMMIT_SHORT_SHA }}'
                        )
                    },
                    {
                        'name': 'Update Image Tag in prod-values.yaml',
                        'run': (
                            f'sed -i "s/^  tag:.*/  tag: ${{{{ env.COMMIT_SHORT_SHA }}}}/" {helm_chart_dir}/prod-values.yaml\n'
                            'git config --global user.email "github-actions[bot]@users.noreply.github.com"\n'
                            'git config --global user.name "github-actions[bot]"\n'
                            'git add .\n'
                            'git commit -m "Update image tag to commit ${{ github.sha }}"\n'
                            'git push origin ${{ github.ref }}'
                        )
                    }
                ]
            }
        }
    }
    return yaml.dump(pipeline, default_flow_style=False)
