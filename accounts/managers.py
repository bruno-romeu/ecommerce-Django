# accounts/managers.py
from django.contrib.auth.base_user import BaseUserManager

class CustomUserManager(BaseUserManager):
    """
    Gerente de modelo de utilizador customizado onde o email é o identificador único
    para autenticação em vez de nomes de utilizador.
    """
    def create_user(self, email, password, **extra_fields):
        """
        Cria e salva um utilizador com o email e senha fornecidos.
        """
        if not email:
            raise ValueError('O Email deve ser definido')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Cria e salva um super-utilizador com o email e senha fornecidos.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)