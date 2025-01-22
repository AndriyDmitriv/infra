from django import forms

class HelmChartForm(forms.Form):
    app_name = forms.CharField(label="Назва додатка", max_length=100)
    replica_count = forms.IntegerField(label="Кількість реплік", initial=1, min_value=1)
    image_repository = forms.CharField(label="Репозиторій Docker-образу", max_length=200)
    image_tag = forms.CharField(label="Тег Docker-образу", max_length=50, initial="latest")
    service_type = forms.ChoiceField(
        label="Тип сервісу",
        choices=[("ClusterIP", "ClusterIP"), ("NodePort", "NodePort"), ("LoadBalancer", "LoadBalancer")],
    )
    service_port = forms.IntegerField(label="Порт сервісу", initial=80)
    target_port = forms.IntegerField(label="Цільовий порт", initial=8080)
    hpa_enabled = forms.BooleanField(label="Увімкнути HPA", required=False)
    hpa_min_replicas = forms.IntegerField(label="Мінімальна кількість реплік", required=False, initial=1)
    hpa_max_replicas = forms.IntegerField(label="Максимальна кількість реплік", required=False, initial=5)
    hpa_target_cpu = forms.IntegerField(label="Цільове завантаження CPU (%)", required=False, initial=80)



class GitSyncForm(forms.Form):
    branch_name = forms.CharField(
        label="Назва гілки",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'main'}),
    )
