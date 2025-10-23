from django.contrib import admin
from .models import Lista, Cargo, Candidato
# Register your models here.
admin.site.register(Lista)
admin.site.register(Candidato)
admin.site.register(Cargo)