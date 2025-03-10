# Generated by Django 5.1.5 on 2025-01-19 17:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0002_rename_api_key_userprofile_aws_access_key_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='git_private_key',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='git_repository',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='aws_access_key',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='aws_secret_key',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='azure_client_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='azure_client_secret',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='azure_subscription_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='azure_tenant_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='cloud_provider',
            field=models.CharField(blank=True, choices=[('aws', 'AWS'), ('gcp', 'GCP'), ('azure', 'Azure')], max_length=50, null=True),
        ),
    ]
