from django.db import models
from django.urls import reverse
from django.utils import timezone

class Categoria(models.Model):
    """
    Modelo para categorizar las noticias
    """
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Noticia(models.Model):
    """
    Modelo principal para las noticias
    """
    ESTADOS = (
        ('borrador', 'Borrador'),
        ('publicado', 'Publicado'),
        ('archivado', 'Archivado'),
    )

    titulo = models.CharField('Título', max_length=200)
    contenido = models.TextField('Contenido')
    resumen = models.TextField('Resumen', max_length=500, blank=True, null=True, help_text='Resumen breve de la noticia (máx. 500 caracteres)')
    imagen = models.ImageField('Imagen', upload_to='noticias/', blank=True, null=True, help_text='Imagen de la noticia (recomendado 1200x630px)')
    destacada = models.BooleanField('¿Destacada?', default=False)
    estado = models.CharField('Estado', max_length=10, choices=ESTADOS, default='borrador')
    fecha_publicacion = models.DateTimeField('Fecha de publicación', default=timezone.now)
    fecha_creacion = models.DateTimeField('Fecha de creación', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('Última actualización', auto_now=True)
    categoria = models.ForeignKey(Categoria, verbose_name='Categoría', on_delete=models.SET_NULL, null=True, blank=True, related_name='noticias')
    visitas = models.PositiveIntegerField('Número de visitas', default=0, editable=False)

    class Meta:
        verbose_name = 'Noticia'
        verbose_name_plural = 'Noticias'
        ordering = ['-fecha_publicacion']
        indexes = [
            models.Index(fields=['-fecha_publicacion']),
        ]

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse('noticias:detalle', args=[self.id])
        
    def incrementar_visitas(self):
        """Incrementa el contador de visitas en 1 y guarda el cambio"""
        self.visitas += 1
        self.save(update_fields=['visitas'])


