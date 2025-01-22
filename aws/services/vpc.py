import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import time
import ipaddress

class VPCService:
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

    def get_regions(self):
        """Отримати список доступних регіонів."""
        try:
            response = self.ec2.describe_regions()
            return [(region['RegionName'], region['RegionName']) for region in response['Regions']]
        except Exception as e:
            raise Exception(f"Помилка отримання регіонів: {str(e)}")

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

    def create_vpc(self, cidr_block, subnet_count, vpc_name='MyVPC'):
        """
        Створити новий VPC з сабнетами, NAT Gateway, Internet Gateway і маршрутними таблицями.

        :param cidr_block: CIDR-блок для VPC, наприклад, "10.0.0.0/16".
        :param subnet_count: Кількість сабнетів (половина буде приватними, половина - публічними).
        :param vpc_name: Назва VPC.
        :return: Ідентифікатор VPC і список сабнетів.
        """
        try:
            # Створення VPC
            vpc_response = self.ec2.create_vpc(CidrBlock=cidr_block)
            vpc_id = vpc_response['Vpc']['VpcId']
            self.ec2.create_tags(Resources=[vpc_id], Tags=[{'Key': 'Name', 'Value': vpc_name}])

            # Створення Internet Gateway
            igw_response = self.ec2.create_internet_gateway()
            igw_id = igw_response['InternetGateway']['InternetGatewayId']
            self.ec2.attach_internet_gateway(VpcId=vpc_id, InternetGatewayId=igw_id)

            # Створення маршрутної таблиці для публічних сабнетів
            public_route_table_response = self.ec2.create_route_table(VpcId=vpc_id)
            public_route_table_id = public_route_table_response['RouteTable']['RouteTableId']
            self.ec2.create_route(
                RouteTableId=public_route_table_id,
                DestinationCidrBlock='0.0.0.0/0',
                GatewayId=igw_id
            )

            # Розрахунок кількості приватних і публічних сабнетів
            public_subnets_count = subnet_count // 2
            private_subnets_count = subnet_count - public_subnets_count

            # Розрахунок CIDR-блоків
            network = ipaddress.ip_network(cidr_block, strict=False)
            subnets = list(network.subnets(new_prefix=24))  # Ділимо на /24
            if len(subnets) < subnet_count:
                raise Exception("Недостатньо CIDR-блоків для заданої кількості сабнетів.")

            all_subnets = []
            azs = self.ec2.describe_availability_zones()['AvailabilityZones']
            azs_cycle = (az['ZoneName'] for az in azs)

            # Створення публічних сабнетів
            for i in range(public_subnets_count):
                az = next(azs_cycle)
                subnet_cidr = str(subnets.pop(0))
                subnet_response = self.ec2.create_subnet(VpcId=vpc_id, CidrBlock=subnet_cidr, AvailabilityZone=az)
                subnet_id = subnet_response['Subnet']['SubnetId']
                all_subnets.append({'SubnetId': subnet_id, 'Type': 'Public', 'CidrBlock': subnet_cidr})
                self.ec2.create_tags(Resources=[subnet_id], Tags=[{'Key': 'Name', 'Value': f'PublicSubnet-{i+1}'}])
                self.ec2.associate_route_table(RouteTableId=public_route_table_id, SubnetId=subnet_id)
                self.ec2.modify_subnet_attribute(SubnetId=subnet_id, MapPublicIpOnLaunch={"Value": True})


            # Створення приватних сабнетів
            for i in range(private_subnets_count):
                az = next(azs_cycle)
                subnet_cidr = str(subnets.pop(0))
                subnet_response = self.ec2.create_subnet(VpcId=vpc_id, CidrBlock=subnet_cidr, AvailabilityZone=az)
                subnet_id = subnet_response['Subnet']['SubnetId']
                all_subnets.append({'SubnetId': subnet_id, 'Type': 'Private', 'CidrBlock': subnet_cidr})
                self.ec2.create_tags(Resources=[subnet_id], Tags=[{'Key': 'Name', 'Value': f'PrivateSubnet-{i+1}'}])

                # Прив'язка NAT Gateway до приватних сабнетів
                nat_eip_response = self.ec2.allocate_address(Domain='vpc')
                nat_eip_id = nat_eip_response['AllocationId']
                nat_gw_response = self.ec2.create_nat_gateway(SubnetId=subnet_id, AllocationId=nat_eip_id)
                nat_gw_id = nat_gw_response['NatGateway']['NatGatewayId']

                # Чекаємо, поки NAT Gateway стане доступним
                waiter = self.ec2.get_waiter('nat_gateway_available')
                waiter.wait(NatGatewayIds=[nat_gw_id])

                private_route_table_response = self.ec2.create_route_table(VpcId=vpc_id)
                private_route_table_id = private_route_table_response['RouteTable']['RouteTableId']
                self.ec2.create_route(
                    RouteTableId=private_route_table_id,
                    DestinationCidrBlock='0.0.0.0/0',
                    NatGatewayId=nat_gw_id
                )
                self.ec2.associate_route_table(RouteTableId=private_route_table_id, SubnetId=subnet_id)

            return vpc_id, all_subnets
        except Exception as e:
            raise Exception(f"Помилка створення VPC: {str(e)}")

