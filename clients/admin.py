from django.contrib import admin
from .models import Client

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'cpf', 'birthday', 'phone',)
    list_filter = ('user', 'id','cpf',)
    search_fields = ('user', 'id','cpf',)

