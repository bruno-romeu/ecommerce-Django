from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings


class SupabaseStorage(S3Boto3Storage):
    location = 'images'
    default_acl = 'public-read'
    file_overwrite = False

    def __init__(self, **kwargs):

        kwargs['endpoint_url'] = settings.AWS_S3_ENDPOINT_URL
        kwargs['region_name'] = settings.AWS_S3_REGION_NAME
        kwargs['access_key'] = settings.AWS_ACCESS_KEY_ID
        kwargs['secret_key'] = settings.AWS_SECRET_ACCESS_KEY
        kwargs['bucket_name'] = settings.AWS_STORAGE_BUCKET_NAME
        kwargs['custom_domain'] = settings.AWS_S3_CUSTOM_DOMAIN

        kwargs['addressing_style'] = "path"
        kwargs['signature_version'] = "s3v4"

        super().__init__(**kwargs)