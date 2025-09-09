from django.contrib import admin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'cpf', 'birthday', 'phone_number',)
    list_filter = ('email', 'id','cpf',)
    search_fields = ('email', 'id','cpf',)

