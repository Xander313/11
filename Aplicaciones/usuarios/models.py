from django.db import models
from django.contrib.auth.models import AbstractUser

from Aplicaciones.periodo.models import Periodo

 # Asegúrate de importar tu modelo Periodo

class Roles(models.Model):
    nombre_rol = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre_rol


class Usuarios(AbstractUser):
    username = models.CharField('Cédula', max_length=10, unique=True)  # se usa como login
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(unique=True)
    id_rol = models.ForeignKey(Roles,  on_delete=models.CASCADE, null=True, blank=True)
    activo = models.BooleanField(default=True)
    imagen = models.ImageField(upload_to='perfil/', blank=True, null=True)
    periodo = models.ForeignKey(Periodo, on_delete=models.SET_NULL, null=True, blank=True)
    plain_password = models.CharField(max_length=128, blank=True, null=True)  # Nuevo campo para contraseña en texto plano
    primer_inicio = models.BooleanField(default=True)
    
    USERNAME_FIELD = 'username'  # la cédula será usada para login
    REQUIRED_FIELDS = ['email', 'nombre', 'apellido']

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        db_table = 'usuarios'

    def __str__(self):
        return f"{self.nombre} {self.apellido or ''} - {self.username}"
