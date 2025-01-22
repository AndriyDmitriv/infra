import boto3
import json
from botocore.exceptions import NoCredentialsError, PartialCredentialsError


class EKSService:
    def __init__(self, access_key, secret_key, region='us-east-1'):
        if not access_key or not secret_key:
            raise Exception("Облікові дані AWS відсутні.")
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.ec2 = boto3.client(
            'ec2',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region
        )
        self.eks = boto3.client(
            'eks',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region
        )
        self.iam = boto3.client(
            'iam',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region
        )

    def set_region(self, region):
        """Оновити регіон."""
        self.region = region
        self.ec2 = boto3.client(
            'ec2',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region
        )
        self.eks = boto3.client(
            'eks',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region
        )
        self.iam = boto3.client(
            'iam',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region
        )

    def get_regions(self):
        """Отримати список доступних регіонів."""
        response = self.ec2.describe_regions()
        return [(region['RegionName'], region['RegionName']) for region in response['Regions']]

    def get_vpcs(self):
        """Отримати список VPC."""
        try:
            response = self.ec2.describe_vpcs()
            return [
                {
                    'VpcId': vpc['VpcId'],
                    'CidrBlock': vpc['CidrBlock']
                }
                for vpc in response['Vpcs']
            ]
        except Exception as e:
            raise Exception(f"Помилка отримання VPC: {str(e)}")

    def get_subnets_by_type(self, vpc_id, subnet_type):
        """Отримати сабнети за типом (публічний/приватний)."""
        try:
            subnets = self.ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['Subnets']
            if subnet_type == 'public':
                return [subnet for subnet in subnets if self.is_public_subnet(subnet['SubnetId'])]
            elif subnet_type == 'private':
                return [subnet for subnet in subnets if not self.is_public_subnet(subnet['SubnetId'])]
            else:
                raise ValueError("Невідомий тип сабнету")
        except Exception as e:
            raise Exception(f"Помилка отримання сабнетів: {str(e)}")

    def is_public_subnet(self, subnet_id):
        """Перевірити, чи сабнет є публічним."""
        try:
            route_tables = self.ec2.describe_route_tables(Filters=[{'Name': 'association.subnet-id', 'Values': [subnet_id]}])
            for route_table in route_tables['RouteTables']:
                for route in route_table['Routes']:
                    if 'GatewayId' in route and route['GatewayId'].startswith('igw-'):
                        return True
            return False
        except Exception as e:
            raise Exception(f"Помилка перевірки сабнету: {str(e)}")

    def get_instance_types(self):
        """Отримати список популярних типів інстансів."""
        return [
            ('t2.micro', 't2.micro (1 vCPU, 1GB RAM)'),
            ('t2.small', 't2.small (1 vCPU, 2GB RAM)'),
            ('t2.medium', 't2.medium (2 vCPU, 4GB RAM)')
        ]

    def get_eks_role_arn(self):
        """Отримати або створити IAM роль для EKS кластера."""
        try:
            response = self.iam.get_role(RoleName="EKSClusterRole")
            return response['Role']['Arn']
        except self.iam.exceptions.NoSuchEntityException:
            return self.create_eks_cluster_role()

    def get_eks_node_role_arn(self):
        """Отримати або створити IAM роль для нод-пулів."""
        try:
            response = self.iam.get_role(RoleName="EKSNodeRole")
            return response['Role']['Arn']
        except self.iam.exceptions.NoSuchEntityException:
            return self.create_eks_node_role()

    def create_eks_cluster(self, cluster_name, vpc_id, subnets, cluster_type):
        """Створити EKS кластер."""
        try:
            response = self.eks.create_cluster(
                name=cluster_name,
                roleArn=self.get_eks_role_arn(),
                resourcesVpcConfig={
                    'subnetIds': [subnet['SubnetId'] for subnet in subnets],
                    'endpointPublicAccess': cluster_type == 'public',
                    'endpointPrivateAccess': cluster_type == 'private'
                }
            )

            # Очікування стану кластера ACTIVE
            waiter = self.eks.get_waiter('cluster_active')
            waiter.wait(name=cluster_name)
            return f"Кластер {cluster_name} успішно створено!"
        except Exception as e:
            raise Exception(f"Помилка створення EKS кластеру: {str(e)}")

    def create_node_group(self, cluster_name, node_group_name, instance_type, node_count, subnets):
        """Створити нод-пул."""
        try:
            response = self.eks.create_nodegroup(
                clusterName=cluster_name,
                nodegroupName=node_group_name,
                scalingConfig={
                    'minSize': 1,
                    'maxSize': node_count,
                    'desiredSize': node_count
                },
                subnets=[subnet['SubnetId'] for subnet in subnets],
                instanceTypes=[instance_type],
                nodeRole=self.get_eks_node_role_arn()
            )
            return f"Нод-пул {node_group_name} успішно створено!"
        except Exception as e:
            raise Exception(f"Помилка створення нод-пулу: {str(e)}")


    def get_clusters(self):
        """Отримати список існуючих кластерів."""
        try:
            clusters = self.eks.list_clusters()['clusters']
            return [{'name': cluster} for cluster in clusters]
        except Exception as e:
            raise Exception(f"Помилка отримання списку кластерів: {str(e)}")

    def get_subnets_from_cluster(self, cluster_name):
        """Отримати сабнети, пов’язані з EKS кластером."""
        try:
            cluster = self.eks.describe_cluster(name=cluster_name)['cluster']
            return [
                {'SubnetId': subnet_id}
                for subnet_id in cluster['resourcesVpcConfig']['subnetIds']
            ]
        except Exception as e:
            raise Exception(f"Помилка отримання сабнетів із кластера: {str(e)}")



    def create_eks_cluster_role(self, role_name="EKSClusterRole"):
        """Створити IAM роль для EKS кластера."""
        try:
            assume_role_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "eks.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
            response = self.iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(assume_role_policy),
                Description="Role for EKS Cluster"
            )
            self.iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn="arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
            )
            self.iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn="arn:aws:iam::aws:policy/AmazonEKSServicePolicy"
            )
            return response['Role']['Arn']
        except Exception as e:
            raise Exception(f"Помилка створення IAM ролі для кластера: {str(e)}")

    def create_eks_node_role(self, role_name="EKSNodeRole"):
        """Створити IAM роль для нод-пулів."""
        try:
            assume_role_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "ec2.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
            response = self.iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(assume_role_policy),
                Description="Role for EKS Node Group"
            )
            self.iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn="arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
            )
            self.iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn="arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
            )
            self.iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn="arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
            )
            return response['Role']['Arn']
        except Exception as e:
            raise Exception(f"Помилка створення IAM ролі для нод-пулів: {str(e)}")
