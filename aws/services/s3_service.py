import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

class S3Service:
    def __init__(self, access_key, secret_key, region='us-east-1'):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )

    def list_buckets(self):
        """Отримати список бакетів."""
        try:
            response = self.s3.list_buckets()
            return [bucket['Name'] for bucket in response['Buckets']]
        except (NoCredentialsError, PartialCredentialsError) as e:
            return f"Помилка автентифікації: {str(e)}"

    def create_bucket(self, bucket_name):
        """Створити бакет."""
        try:
            self.s3.create_bucket(Bucket=bucket_name)
            return f"Бакет {bucket_name} успішно створений."
        except Exception as e:
            return f"Помилка створення бакета: {str(e)}"

    def upload_file(self, bucket_name, file_path, object_name=None):
        """Завантажити файл у S3."""
        if object_name is None:
            object_name = file_path.split('/')[-1]

        try:
            self.s3.upload_file(file_path, bucket_name, object_name)
            return f"Файл {file_path} завантажено як {object_name} у бакет {bucket_name}."
        except Exception as e:
            return f"Помилка завантаження файлу: {str(e)}"
