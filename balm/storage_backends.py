from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings


class SupabaseStorage(S3Boto3Storage):
    location = 'images'
    default_acl = 'public-read'
    file_overwrite = False

    def __init__(self, **kwargs):
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        self.endpoint_url = settings.AWS_S3_ENDPOINT_URL
        self.access_key = settings.AWS_ACCESS_KEY_ID
        self.secret_key = settings.AWS_SECRET_ACCESS_KEY
        self.region_name = settings.AWS_S3_REGION_NAME
        self.custom_domain = settings.AWS_S3_CUSTOM_DOMAIN

        self.addressing_style = "path"
        self.signature_version = "s3v4"
        super().__init__(**kwargs)