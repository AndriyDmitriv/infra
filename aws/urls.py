from django.urls import path
from . import views

app_name = 'aws'

urlpatterns = [
    path('dashboard/', views.aws_dashboard, name='dashboard'),
    path('ec2/create/', views.aws_create_instance, name='ec2_create'),
    path('get-vpcs-and-subnets/', views.get_vpcs_and_subnets, name='get_vpcs_and_subnets'),
    path('s3/', views.s3_list, name='s3_list'),
    path('s3/create/', views.s3_create, name='s3_create'),
    path('ec2/', views.ec2_list, name='ec2_list'),
    path('vpc/', views.vpc_list, name='vpc_list'),
    path('vpc/create', views.aws_create_vpc, name='vpc_create'),
    path('eks/', views.eks_list, name='eks_list'),
    path('eks/create', views.aws_create_eks_cluster, name='aws_create_eks'),
    path('eks/create-nodegroup/', views.aws_create_eks_nodegroup, name='aws_create_eks_nodegroup'),
]
