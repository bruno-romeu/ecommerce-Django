from django.core.files.storage import Storage
from django.conf import settings
from django.utils.text import slugify
from django.utils.deconstruct import deconstructible
from supabase import create_client, Client
from io import BytesIO
import os
import uuid
import mimetypes
import datetime


@deconstructible
class SupabaseStorage(Storage):
    def __init__(self):
        self.supabase_url = settings.SUPABASE_URL
        self.supabase_key = settings.SUPABASE_KEY
        self.bucket_name = settings.SUPABASE_BUCKET_NAME
        self.client: Client = create_client(self.supabase_url,
                                            self.supabase_key)

    def _sanitize_filename(self, name):
        """Sanitiza o nome do arquivo para ser compatível com Supabase"""
        dir_name, file_name = os.path.split(name)

        file_root, file_ext = os.path.splitext(file_name)

        clean_name = slugify(file_root)

        if not clean_name:
            clean_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        sanitized = os.path.join(dir_name,
                                 f"{clean_name}{file_ext.lower()}")

        return sanitized

    def _get_content_type(self, name):
        """Detecta o content type do arquivo"""
        content_type, _ = mimetypes.guess_type(name)
        return content_type or 'application/octet-stream'

    def _save(self, name, content):
        """Salva o arquivo no Supabase Storage"""
        try:
            name = self._sanitize_filename(name)
            if hasattr(content,
                       'read'):
                file_content = content.read()
            else:
                file_content = content

            content_type = self._get_content_type(name)

            response = self.client.storage.from_(self.bucket_name).upload(
                path=name,
                file=file_content,
                file_options={
                    "content-type": content_type,
                    "upsert": "false"
                }
            )

            return name

        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                name = self.get_available_name(name)
                return self._save(name,
                                  content)
            raise e

    def _open(self, name, mode='rb'):
        """Abre e retorna o arquivo do Supabase"""
        try:
            response = self.client.storage.from_(self.bucket_name).download(name)
            return BytesIO(response)
        except Exception as e:
            raise FileNotFoundError(f"Arquivo {name} não encontrado: {e}")

    def exists(self, name):
        """Verifica se o arquivo existe no Supabase"""
        try:
            response = self.client.storage.from_(self.bucket_name).list(
                path=os.path.dirname(name) or ''
            )

            filename = os.path.basename(name)
            return any(item['name'] == filename for item in response)
        except:
            return False

    def delete(self, name):
        """Deleta o arquivo do Supabase"""
        try:
            self.client.storage.from_(self.bucket_name).remove([name])
        except Exception as e:
            print(f"Erro ao deletar arquivo {name}: {e}")

    def url(self, name):
        """Retorna a URL pública do arquivo"""
        project_id = self.supabase_url.split('//')[1].split('.')[0]
        return f"https://{project_id}.supabase.co/storage/v1/object/public/{self.bucket_name}/{name}"

    def size(self, name):
        """Retorna o tamanho do arquivo"""
        try:
            response = self.client.storage.from_(self.bucket_name).list(
                path=os.path.dirname(name) or ''
            )
            filename = os.path.basename(name)
            for item in response:
                if item['name'] == filename:
                    return item.get('metadata',
                                    {}).get('size',
                                            0)
            return 0
        except:
            return 0

    def get_available_name(self, name, max_length=None):
        """Gera um nome único se o arquivo já existir"""
        name = self._sanitize_filename(name)

        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)

        count = 1
        while self.exists(name):
            name = os.path.join(dir_name,
                                f"{file_root}_{count}{file_ext}")
            count += 1

            if max_length and len(name) > max_length:
                raise Exception(f"Nome do arquivo muito longo: {name}")

        return name