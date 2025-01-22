from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from dashboard.models import UserProfile
from .services.s3_service import S3Service
from .services.ec2_service import EC2Service
from django.http import JsonResponse
from .services.vpc import VPCService
from .services.eks import EKSService



@login_required
def aws_dashboard(request):
    # Отримання профілю користувача
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if not profile.aws_access_key or not profile.aws_secret_key:
        return render(request, 'aws/dashboard.html', {
            'error': 'Будь ласка, додайте ваші AWS ключі в налаштуваннях профілю.'
        })

    # Ініціалізація сервісів S3 та EC2
    try:
        s3_service = S3Service(profile.aws_access_key, profile.aws_secret_key)
        ec2_service = EC2Service(profile.aws_access_key, profile.aws_secret_key)

        # Отримання списку бакетів та інстансів
        buckets = s3_service.list_buckets()
        instances = ec2_service.list_instances()

        return render(request, 'aws/dashboard.html', {
            'buckets': buckets,
            'instances': instances
        })

    except Exception as e:
        return render(request, 'aws/dashboard.html', {
            'error': f'Помилка підключення до AWS: {str(e)}'
        })


@login_required
def aws_create_instance(request):
    profile = UserProfile.objects.get(user=request.user)

    if not profile.aws_access_key or not profile.aws_secret_key:
        return render(request, 'aws/create_instance.html', {
            'error': 'Будь ласка, додайте ваші AWS ключі в налаштуваннях профілю.'
        })

    ec2_service = EC2Service(profile.aws_access_key, profile.aws_secret_key)

    if request.method == 'POST':
        region = request.POST.get('region')
        vpc_id = request.POST.get('vpc_id')
        subnet_id = request.POST.get('subnet_id')
        instance_type = request.POST.get('instance_type')
        ami_id = request.POST.get('ami_id')
        volume_size = int(request.POST.get('volume_size', 8))
        instance_name = request.POST.get('instance_name', 'MyInstance')
        ports = list(map(int, request.POST.get('ports', '').split(',')))
        ssh_key_name = request.POST.get('ssh_key_name')
        ssh_key_material = request.POST.get('ssh_key_material')

        try:
            ec2_service.set_region(region)

            if ssh_key_material:
                ssh_key_name = f"{instance_name}-key"
                ec2_service.ec2.import_key_pair(KeyName=ssh_key_name, PublicKeyMaterial=ssh_key_material)
            elif not ssh_key_name:
                ssh_key_name = f"{instance_name}-key"
                key_pair = ec2_service.create_key_pair(ssh_key_name)
                with open(f"{ssh_key_name}.pem", 'w') as key_file:
                    key_file.write(key_pair['KeyMaterial'])

            sg_id = ec2_service.create_security_group(f"{instance_name}-sg", "Security Group", vpc_id)
            ec2_service.authorize_security_group(sg_id, ports)

            instance_id = ec2_service.create_instance(
                instance_type=instance_type,
                ami_id=ami_id,
                volume_size=volume_size,
                instance_name=instance_name,
                ssh_key_name=ssh_key_name,
                sg_id=sg_id,
                subnet_id=subnet_id
            )

            return render(request, 'aws/create_instance.html', {
                'success': f'EC2 інстанс створено з ID: {instance_id}'
            })
        except Exception as e:
            return render(request, 'aws/create_instance.html', {
                'error': f'Помилка створення інстансу: {str(e)}'
            })

    else:
        try:
            regions = ec2_service.get_regions()
            vpcs = ec2_service.get_vpcs()
            subnets = ec2_service.get_subnets(vpcs[0]['VpcId']) if vpcs else []
            instance_types = ec2_service.get_instance_types()
            amis = ec2_service.get_amis()
        except Exception as e:
            return render(request, 'aws/create_instance.html', {
                'error': f'Помилка завантаження даних: {str(e)}'
            })

        return render(request, 'aws/create_instance.html', {
            'regions': regions,
            'vpcs': vpcs,
            'subnets': subnets,
            'instance_types': instance_types,
            'amis': amis
        })

@login_required
def get_vpcs_and_subnets(request):
    """Отримати VPC та сабнети для вибраного регіону."""
    import logging
    logger = logging.getLogger(__name__)

    region = request.GET.get('region')
    logger.info(f"Отримання VPC та Сабнетів для регіону: {region}")

    profile = UserProfile.objects.get(user=request.user)

    if not profile.aws_access_key or not profile.aws_secret_key:
        logger.error("AWS ключі не знайдено.")
        return JsonResponse({'error': 'AWS ключі не знайдено.'}, status=400)

    try:
        ec2_service = EC2Service(profile.aws_access_key, profile.aws_secret_key, region=region)
        vpcs = ec2_service.get_vpcs()
        logger.info(f"Отримано VPC: {vpcs}")
        
        subnets = []
        if vpcs:
            subnets = ec2_service.get_subnets(vpcs[0]['VpcId'])
            logger.info(f"Отримано Сабнети: {subnets}")
        
        return JsonResponse({'vpcs': vpcs, 'subnets': subnets}, safe=False)
    except Exception as e:
        logger.error(f"Помилка: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)





@login_required
def aws_create_vpc(request):
    # Отримуємо профіль користувача
    profile = UserProfile.objects.get(user=request.user)

    # Перевірка наявності AWS ключів
    if not profile.aws_access_key or not profile.aws_secret_key:
        return render(request, 'aws/create_vpc.html', {
            'error': 'Будь ласка, додайте ваші AWS ключі в налаштуваннях профілю.'
        })

    vpc_service = VPCService(profile.aws_access_key, profile.aws_secret_key)

    if request.method == 'POST':
        # Зчитування даних з форми
        vpc_name = request.POST.get('vpc_name', 'MyVPC')  # За замовчуванням MyVPC
        cidr_block = request.POST.get('cidr_block', '10.0.0.0/16')
        subnet_count = int(request.POST.get('subnet_count', 2))

        try:
            # Створення VPC
            vpc_id, subnets = vpc_service.create_vpc(cidr_block, subnet_count, vpc_name)

            return render(request, 'aws/create_vpc.html', {
                'success': f"VPC '{vpc_name}' створено з ID: {vpc_id}",
                'subnets': subnets
            })
        except Exception as e:
            return render(request, 'aws/create_vpc.html', {
                'error': f"Помилка створення VPC: {str(e)}"
            })

    else:
        # Підготовка даних для форми
        try:
            regions = vpc_service.get_regions()
        except Exception as e:
            return render(request, 'aws/create_vpc.html', {
                'error': f"Помилка завантаження даних: {str(e)}"
            })

        return render(request, 'aws/create_vpc.html', {'regions': regions})






@login_required
def aws_create_eks_cluster(request):
    """Функція для створення EKS кластеру."""
    profile = UserProfile.objects.get(user=request.user)
    eks_service = EKSService(profile.aws_access_key, profile.aws_secret_key)

    if request.method == 'POST':
        region = request.POST.get('region')
        vpc_id = request.POST.get('vpc_id')
        cluster_name = request.POST.get('cluster_name')
        cluster_type = request.POST.get('cluster_type')  # 'public' або 'private'

        try:
            eks_service.set_region(region)
            subnets = eks_service.get_subnets_by_type(vpc_id, cluster_type)

            if not subnets:
                return render(request, 'aws/create_eks_cluster.html', {
                    'error': 'Не вдалося знайти сабнети для обраного VPC та типу кластера.'
                })

            eks_service.create_eks_cluster(cluster_name, vpc_id, subnets, cluster_type)
            return render(request, 'aws/create_eks_cluster.html', {
                'success': f'Кластер {cluster_name} успішно створено!',
                'regions': eks_service.get_regions(),
                'vpcs': eks_service.get_vpcs(),
            })

        except Exception as e:
            return render(request, 'aws/create_eks_cluster.html', {'error': str(e)})

    else:
        try:
            regions = eks_service.get_regions()
            vpcs = eks_service.get_vpcs()

            return render(request, 'aws/create_eks_cluster.html', {
                'regions': regions,
                'vpcs': vpcs,
            })

        except Exception as e:
            return render(request, 'aws/create_eks_cluster.html', {'error': str(e)})




@login_required
def aws_create_eks_nodegroup(request):
    """Функція для створення нод-пулу в існуючому кластері."""
    profile = UserProfile.objects.get(user=request.user)
    eks_service = EKSService(profile.aws_access_key, profile.aws_secret_key)

    if request.method == 'POST':
        region = request.POST.get('region')
        cluster_name = request.POST.get('cluster_name')
        node_group_name = request.POST.get('node_group_name')
        instance_type = request.POST.get('instance_type')
        node_count = int(request.POST.get('node_count', 1))

        try:
            eks_service.set_region(region)
            subnets = eks_service.get_subnets_from_cluster(cluster_name)

            if not subnets:
                return render(request, 'aws/create_eks_nodegroup.html', {
                    'error': 'Не вдалося знайти сабнети, пов’язані з кластером.'
                })

            eks_service.create_node_group(cluster_name, node_group_name, instance_type, node_count, subnets)
            return render(request, 'aws/create_eks_nodegroup.html', {
                'success': f'Нод-пул {node_group_name} успішно створено!',
                'regions': eks_service.get_regions(),
                'clusters': eks_service.get_clusters(),
                'instance_types': eks_service.get_instance_types(),
            })

        except Exception as e:
            return render(request, 'aws/create_eks_nodegroup.html', {'error': str(e)})

    else:
        try:
            regions = eks_service.get_regions()
            clusters = eks_service.get_clusters()
            instance_types = eks_service.get_instance_types()

            return render(request, 'aws/create_eks_nodegroup.html', {
                'regions': regions,
                'clusters': clusters,
                'instance_types': instance_types,
            })

        except Exception as e:
            return render(request, 'aws/create_eks_nodegroup.html', {'error': str(e)})




@login_required
def s3_list(request):
    # Логіка для отримання списку бакетів
    return render(request, 'aws/s3_list.html')

@login_required
def s3_create(request):
    # Логіка для створення нового бакета
    return render(request, 'aws/s3_create.html')

@login_required
def ec2_list(request):
    # Логіка для отримання списку інстансів
    return render(request, 'aws/ec2_list.html')

@login_required
def vpc_list(request):
    # Логіка для отримання списку інстансів
    return render(request, 'aws/ec2_list.html')
@login_required
def eks_list(request):
    # Логіка для отримання списку інстансів
    return render(request, 'aws/ec2_list.html')


