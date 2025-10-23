from django.db import models
from django.utils import timezone
from Aplicaciones.periodo.models import Periodo
from Aplicaciones.padron.models import PadronElectoral
from Aplicaciones.elecciones.models import Candidato, Lista

# Create your models here.
#PENDIENTE OJO

class ProcesoElectoral(models.Model):
    nombre = models.CharField(max_length=200)
    periodo = models.ForeignKey(Periodo, on_delete=models.CASCADE)
    fecha = models.DateField(help_text='Fecha de las elecciones', default=timezone.now)
    hora_inicio = models.TimeField(help_text='Hora de inicio de las elecciones', default=timezone.datetime.strptime('08:00', '%H:%M').time())
    hora_fin = models.TimeField(help_text='Hora de finalización de las elecciones', default=timezone.datetime.strptime('17:00', '%H:%M').time())
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('activo', 'Activo'),
        ('finalizado', 'Finalizado')
    ]
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    descripcion = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def _esta_en_rango_horario(self):
        """Método auxiliar para verificar si la hora actual está en el rango de votación"""
        # Obtener la hora actual en la zona horaria del servidor
        ahora = timezone.localtime(timezone.now())
        print(f"\nVerificando horario para proceso: {self.nombre}")
        print(f"Hora actual (servidor): {ahora}")
        print(f"Fecha actual: {ahora.date()}")
        print(f"Hora actual: {ahora.time()}")
        print(f"Fecha proceso: {self.fecha}")
        print(f"Hora inicio: {self.hora_inicio}")
        print(f"Hora fin: {self.hora_fin}")
        
        # Comparar fechas
        if ahora.date() == self.fecha:
            print("Es el mismo día")
            # Comparar horas
            if self.hora_inicio <= ahora.time() <= self.hora_fin:
                print("Está dentro del rango de horas")
                return True
            else:
                print("NO está dentro del rango de horas")
        else:
            print("NO es el mismo día")
        return False

    def actualizar_estado(self):
        # Obtener la hora actual en la zona horaria del servidor
        ahora = timezone.localtime(timezone.now())
        
        # Si es el mismo día y está en el rango de horas
        if self._esta_en_rango_horario():
            self.estado = 'activo'
        # Si es un día futuro
        elif ahora.date() < self.fecha:
            self.estado = 'pendiente'
        # Si es el mismo día pero antes de la hora de inicio
        elif ahora.date() == self.fecha and ahora.time() < self.hora_inicio:
            self.estado = 'pendiente'
        # En cualquier otro caso (día pasado o mismo día después de hora_fin)
        else:
            self.estado = 'finalizado'
        
        print(f"Estado final para {self.nombre}: {self.estado}")
        self.save()

    def esta_activo(self):
        return self._esta_en_rango_horario()

    def __str__(self):
        return f"{self.nombre} - {self.periodo}"

class Voto(models.Model):
    proceso_electoral = models.ForeignKey(ProcesoElectoral, on_delete=models.CASCADE)
    votante = models.ForeignKey(PadronElectoral, on_delete=models.CASCADE, null=True, blank=True)
    lista = models.ForeignKey(Lista, on_delete=models.CASCADE, null=True, blank=True)
    es_nulo = models.BooleanField(default=False)
    es_blanco = models.BooleanField(default=False)
    fecha_voto = models.DateTimeField(auto_now_add=True)
    hash_voto = models.CharField(max_length=64, unique=True)

    class Meta:
        unique_together = ['proceso_electoral', 'votante']

    def __str__(self):
        if self.es_nulo:
            return f"Voto Nulo - {self.votante}"
        elif self.es_blanco:
            return f"Voto Blanco - {self.votante}"
        else:
            return f"Voto Válido - {self.votante} - {self.lista}"


class CarnetVotacion(models.Model):
    """
    Modelo para almacenar la información del carnet de votación
    """
    voto = models.OneToOneField(Voto, on_delete=models.CASCADE, related_name='carnet', null=True, blank=True)
    codigo_qr = models.CharField(max_length=255, blank=True, help_text='Código QR del voto')
    fecha_emision = models.DateTimeField(auto_now_add=True)
    codigo_verificacion = models.CharField(max_length=64, unique=True, null=True, blank=True, help_text='Código único para verificar el voto')
    
    # Información adicional que se mostrará en el carnet
    nombre_completo = models.CharField(max_length=200, blank=True, null=True)
    cedula = models.CharField(max_length=20, blank=True, null=True)
    proceso_electoral = models.CharField(max_length=200, blank=True, null=True)
    fecha_votacion = models.DateTimeField(null=True, blank=True)
    
    # Campos para control de verificación
    utilizado = models.BooleanField(default=False, help_text='Indica si el carnet ha sido verificado')
    fecha_verificacion = models.DateTimeField(null=True, blank=True, help_text='Fecha y hora de la verificación')
    
    class Meta:
        verbose_name = 'Carnet de Votación'
        verbose_name_plural = 'Carnets de Votación'
        ordering = ['-fecha_emision']
    
    def __str__(self):
        return f"Carnet de {self.nombre_completo} - {self.proceso_electoral}"