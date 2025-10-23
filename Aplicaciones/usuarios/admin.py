from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Roles, Usuarios
# Register your models here.

class CustomUserAdmin(UserAdmin):
    model = Usuarios
    list_display = ('email', 'nombre', 'apellido', 'is_staff', 'is_active')
    search_fields = ('email', 'nombre', 'apellido')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('nombre', 'apellido')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
    )

admin.site.register(Usuarios, CustomUserAdmin)
admin.site.register(Roles,)
