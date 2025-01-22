from django import forms
from .services.ec2_service import EC2Service

class EC2InstanceForm(forms.Form):
    def __init__(self, *args, **kwargs):
        ec2_service = kwargs.pop('ec2_service')
        super().__init__(*args, **kwargs)

        # Динамічно отримуємо регіони, типи інстансів та AMI
        self.fields['region'].choices = ec2_service.get_regions()
        self.fields['instance_type'].choices = ec2_service.get_instance_types()
        self.fields['ami'].choices = ec2_service.get_amis()

    region = forms.ChoiceField(label="Регіон", widget=forms.Select(attrs={'class': 'form-control'}))
    instance_type = forms.ChoiceField(label="Тип інстанса", widget=forms.Select(attrs={'class': 'form-control'}))
    ami = forms.ChoiceField(label="Операційна система (AMI)", widget=forms.Select(attrs={'class': 'form-control'}))
    volume_size = forms.IntegerField(label="Розмір диска (GB)", widget=forms.NumberInput(attrs={'class': 'form-control'}), initial=8)
