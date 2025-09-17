
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Cria um super utilizador de forma não-interativa usando variáveis de ambiente.'

    def handle(self, *args, **options):
        email = os.environ.get('ADMIN_EMAIL')
        password = os.environ.get('ADMIN_PASS')

        if not all([email, password]):
            self.stdout.write(self.style.ERROR('As variáveis de ambiente ADMIN_EMAIL e ADMIN_PASS precisam de ser definidas.'))
            return

        if not User.objects.filter(email=email).exists():
            self.stdout.write(self.style.SUCCESS(f'A criar super utilizador com o email {email}...'))
            User.objects.create_superuser(
                email=email,
                password=password
            )
            self.stdout.write(self.style.SUCCESS('Super utilizador criado com sucesso.'))
        else:
            self.stdout.write(self.style.WARNING(f'Super utilizador com o email {email} já existe.'))