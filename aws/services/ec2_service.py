import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import time

class EC2Service:
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


    def set_region(self, region):
        """Оновити регіон."""
        self.region = region
        self.ec2 = boto3.client(
            'ec2',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region
        )

    def get_vpcs(self):
        """Отримати список VPC."""
        try:
            response = self.ec2.describe_vpcs()
            vpcs = [
                {
                    'VpcId': vpc['VpcId'],
                    'CidrBlock': vpc['CidrBlock'],
                    'State': vpc['State']
                }
                for vpc in response['Vpcs']
            ]
            return vpcs
        except Exception as e:
            raise Exception(f"Помилка отримання VPC: {str(e)}")

    def get_subnets(self, vpc_id):
        """Отримати список сабнетів для VPC."""
        try:
            response = self.ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
            subnets = [
                {
                    'SubnetId': subnet['SubnetId'],
                    'CidrBlock': subnet['CidrBlock'],
                    'AvailabilityZone': subnet['AvailabilityZone']
                }
                for subnet in response['Subnets']
            ]
            return subnets
        except Exception as e:
            raise Exception(f"Помилка отримання сабнетів: {str(e)}")

    def create_key_pair(self, key_name):
        """Створити нову пару SSH ключів."""
        try:
            response = self.ec2.create_key_pair(KeyName=key_name)
            return {
                'KeyName': response['KeyName'],
                'KeyMaterial': response['KeyMaterial']
            }
        except Exception as e:
            raise Exception(f"Помилка створення SSH ключа: {str(e)}")

    def get_regions(self):
        """Отримати список доступних регіонів."""
        response = self.ec2.describe_regions()
        return [(region['RegionName'], region['RegionName']) for region in response['Regions']]

    def get_instance_types(self):
        """Отримати список популярних типів інстансів."""
        return [
            ('t2.micro', 't2.micro (1 vCPU, 1GB RAM)'),
            ('t2.small', 't2.small (1 vCPU, 2GB RAM)'),
            ('t2.medium', 't2.medium (2 vCPU, 4GB RAM)'),
        ]

    def get_amis(self):
        """Отримати список доступних AMI (образів систем)."""
        response = self.ec2.describe_images(Owners=['amazon'])
        amis = [
            (image['ImageId'], f"{image['Name']} ({image['ImageId']})")
            for image in sorted(response['Images'], key=lambda x: x['CreationDate'], reverse=True)
        ]
        return amis[:10] 

    def list_instances(self):
        """Отримати список EC2 інстансів."""
        try:
            response = self.ec2.describe_instances()
            instances = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instances.append({
                        'InstanceId': instance['InstanceId'],
                        'State': instance['State']['Name'],
                        'Type': instance['InstanceType'],
                        'Region': instance['Placement']['AvailabilityZone']
                    })
            return instances
        except Exception as e:
            raise Exception(f"Помилка отримання списку інстансів: {str(e)}")


    def create_security_group(self, group_name, description, vpc_id):
        """Створити групу безпеки."""
        try:
            response = self.ec2.create_security_group(
                GroupName=group_name,
                Description=description,
                VpcId=vpc_id
            )
            return response['GroupId']
        except Exception as e:
            raise Exception(f"Помилка створення Security Group: {str(e)}")

    def authorize_security_group(self, group_id, ports):
        """Відкрити порти в групі безпеки."""
        try:
            for port in ports:
                self.ec2.authorize_security_group_ingress(
                    GroupId=group_id,
                    IpProtocol='tcp',
                    FromPort=port,
                    ToPort=port,
                    CidrIp='0.0.0.0/0'
                )
        except Exception as e:
            raise Exception(f"Помилка авторизації Security Group: {str(e)}")


    def authorize_security_group_ingress(self, group_id, ports):
        """Дозволити трафік для певних портів."""
        try:
            for port in ports:
                self.ec2.authorize_security_group_ingress(
                    GroupId=group_id,
                    IpProtocol='tcp',
                    FromPort=port,
                    ToPort=port,
                    CidrIp='0.0.0.0/0'
                )
        except Exception as e:
            raise Exception(f"Помилка дозволу портів: {str(e)}")

    def create_instance(self, instance_type, ami_id, volume_size, instance_name, ssh_key_name, sg_id, subnet_id):
        """Створити новий EC2 інстанс."""
        try:
            response = self.ec2.run_instances(
                ImageId=ami_id,
                InstanceType=instance_type,
                MinCount=1,
                MaxCount=1,
                KeyName=ssh_key_name,
                SubnetId=subnet_id,
                SecurityGroupIds=[sg_id],
                BlockDeviceMappings=[
                    {
                        'DeviceName': '/dev/xvda',
                        'Ebs': {
                            'VolumeSize': volume_size,
                            'DeleteOnTermination': True,
                            'VolumeType': 'gp2'
                        }
                    }
                ],
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [{'Key': 'Name', 'Value': instance_name}]
                    }
                ]
            )
            instance_id = response['Instances'][0]['InstanceId']
            return instance_id
        except Exception as e:
            raise Exception(f"Помилка створення інстансу: {str(e)}")

