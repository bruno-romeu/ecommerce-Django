""""
from django.db import models
from django.contrib.auth.models import User

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True, null=True)
    cpf = models.CharField(max_length=14, unique=True, null=True)
    birthday = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username or str(self.user)

"""