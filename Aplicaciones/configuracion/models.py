from django.db import models

# Create your models here.
class LogoConfig(models.Model):
    logo_1 = models.ImageField(upload_to='logos/')
    logo_2 = models.ImageField(upload_to='logos/')
    iniciales = models.CharField(max_length=10)

    def __str__(self):
        return self.iniciales

