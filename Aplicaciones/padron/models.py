from django.db import models
from django.core.exceptions import ValidationError
from Aplicaciones.periodo.models import Periodo
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.db.models.signals import pre_save
from django.dispatch import receiver

class Grado(models.Model):
    """Modelo para grados académicos (1ro, 2do, etc.)"""
    nombre = models.CharField(max_length=50)
    periodo = models.ForeignKey(
        Periodo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='grados',
        verbose_name="Período académico"
    )

    class Meta:
        unique_together = ('nombre', 'periodo')
        ordering = ['nombre']
        verbose_name = "Grado"
        verbose_name_plural = "Grados"

    def __str__(self):
        return f"{self.nombre} ({self.periodo.nombre if self.periodo else 'Sin período'})"

class Paralelo(models.Model):
    """Modelo para paralelos (A, B, C) dentro de un grado"""
    nombre = models.CharField(max_length=5, verbose_name="Letra del paralelo")
    grado = models.ForeignKey(
        Grado, 
        on_delete=models.CASCADE, 
        related_name="paralelos",
        verbose_name="Grado asociado"
    )

    class Meta:
        unique_together = ('nombre', 'grado')
        ordering = ['grado', 'nombre']
        verbose_name = "Paralelo"
        verbose_name_plural = "Paralelos"

    def __str__(self):
        return f"{self.grado.nombre}-{self.nombre}"

class PadronElectoral(models.Model):
    """Modelo para el padrón electoral de estudiantes"""
    ESTADOS = [
        ('activo', 'Activo - Puede votar'),
        ('inactivo', 'Inactivo - No puede votar'),
    ]

    # Información personal
    cedula = models.CharField(max_length=10, unique=True, verbose_name="Cédula de identidad")
    nombre = models.CharField(max_length=100, verbose_name="Nombres")
    apellidos = models.CharField(max_length=100, verbose_name="Apellidos")
    correo = models.EmailField(verbose_name="Correo electrónico")
    telefono = models.CharField(max_length=15, blank=True, null=True, verbose_name="Teléfono")
    
    # Relaciones académicas
    periodo = models.ForeignKey(
        Periodo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="padron_electoral",
        verbose_name="Período académico"
    )
    grado = models.ForeignKey(
        Grado,
        on_delete=models.CASCADE,
        verbose_name="Grado del estudiante"
    )
    paralelo = models.ForeignKey(
        Paralelo,
        on_delete=models.CASCADE,
        verbose_name="Paralelo del estudiante"
    )
    
    # Estado y fechas
    estado = models.CharField(
        max_length=10, 
        choices=ESTADOS, 
        default='activo',
        verbose_name="Estado en el padrón"
    )
    fecha_registro = models.DateTimeField(default=timezone.now, verbose_name="Fecha de registro")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    class Meta:
        unique_together = [
            ('cedula', 'periodo'),  # Una cédula sólo puede estar una vez por período
            ('correo', 'periodo')   # Un correo sólo puede estar una vez por período
        ]
        verbose_name = "Registro electoral"
        verbose_name_plural = "Padrón electoral"
        ordering = ['apellidos', 'nombre']

    def __str__(self):
        return f"{self.apellidos} {self.nombre} - {self.grado.nombre}{self.paralelo.nombre}"

    def clean(self):
        """Validaciones para mantener la integridad de los datos"""
        # Verifica que el paralelo pertenezca al grado
        if self.paralelo.grado != self.grado:
            raise ValidationError("El paralelo seleccionado no corresponde al grado especificado")
        
        # Verifica que el grado pertenezca al período (si período existe)
        if self.periodo and self.grado.periodo != self.periodo:
            raise ValidationError("El grado seleccionado no corresponde al período especificado")


class CredencialUsuario(models.Model):
    """Modelo para almacenar las credenciales de los usuarios del sistema"""
    padron = models.OneToOneField(
        PadronElectoral,
        on_delete=models.CASCADE,
        related_name='credencial',
        verbose_name="Registro del padrón"
    )
    
    # Usuario será la cédula del estudiante
    usuario = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Nombre de usuario"
    )
    
    # Contraseña encriptada (se almacena encriptada, pero se puede acceder a la versión en texto plano)
    _contrasena_plana = models.CharField(
        max_length=128,
        verbose_name="Contraseña (texto plano)",
        blank=True,
        null=True,
        help_text="Se almacena temporalmente para mostrarla al administrador"
    )
    contrasena_encriptada = models.CharField(
        max_length=128,
        verbose_name="Contraseña (encriptada)",
        blank=True,
        null=True
    )
    
    fecha_generacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de generación"
    )
    
    # Estado de la credencial
    ESTADOS = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('cambiada', 'Contraseña cambiada')
    ]
    estado = models.CharField(
        max_length=10,
        choices=ESTADOS,
        default='activo',
        verbose_name="Estado de la credencial"
    )
    
    class Meta:
        verbose_name = "Credencial de usuario"
        verbose_name_plural = "Credenciales de usuarios"
        ordering = ['-fecha_generacion']
    
    def __str__(self):
        return f"{self.padron.cedula} - {self.padron.nombre} {self.padron.apellidos}"

    def cambiar_estado(self, nuevo_estado):
        """Cambia el estado de la credencial"""
        if nuevo_estado in dict(self.ESTADOS):
            self.estado = nuevo_estado
            self.save()
            return True
        return False

    def cambiar_contrasena(self, nueva_contrasena):
        """Cambia la contraseña y actualiza el estado"""
        self.contrasena = nueva_contrasena
        self.estado = 'cambiada'
        self.save()
        return True

    def generar_contrasena(self, forzar=False):
        """
        Genera una nueva contraseña aleatoria solo si no existe una previamente
        
        Args:
            forzar (bool): Si es True, genera una nueva contraseña incluso si ya existe una
        """
        # Si ya existe una contraseña y no se está forzando, retornar la existente
        if not forzar and self._contrasena_plana:
            return self._contrasena_plana
            
        import random
        import string
        
        # Generar una contraseña segura con mayúsculas, minúsculas y números
        caracteres = string.ascii_letters + string.digits
        while True:
            nueva_contrasena = ''.join(random.choices(caracteres, k=8))
            # Asegurarse de que tenga al menos un número, una mayúscula y una minúscula
            if (any(c.isdigit() for c in nueva_contrasena) and 
                any(c.isupper() for c in nueva_contrasena) and
                any(c.islower() for c in nueva_contrasena)):
                break
                
        print(f"[DEBUG] Generada nueva contraseña: {nueva_contrasena}")
        
        # Guardar directamente la contraseña en texto plano y generar el hash
        self._contrasena_plana = nueva_contrasena
        self.contrasena_encriptada = make_password(nueva_contrasena)
        
        # Solo establecer como 'activo' si es una nueva cuenta
        if not self.pk:
            self.estado = 'activo'
            
        # Guardar los cambios
        if self.pk:
            # Si ya existe, actualizar solo los campos necesarios
            self.save(update_fields=['_contrasena_plana', 'contrasena_encriptada', 'estado'])
        else:
            # Si es nuevo, guardar todo
            self.save()
            
        print(f"[DEBUG] Contraseña guardada. Texto plano: {self._contrasena_plana}")
        print(f"[DEBUG] Hash generado: {self.contrasena_encriptada}")
        
        return nueva_contrasena

    @property
    def contrasena(self):
        """Propiedad para compatibilidad con código existente"""
        print(f"[DEBUG] Obteniendo contrasena. _contrasena_plana: {self._contrasena_plana}")
        return self._contrasena_plana or ''

    @contrasena.setter
    def contrasena(self, value):
        """Setter para guardar tanto la versión en texto plano como la encriptada"""
        print(f"[DEBUG] Estableciendo contrasena. Valor recibido: {value}")
        if value:  # Solo actualizar si se proporciona un valor
            print(f"[DEBUG] Guardando contraseña en texto plano y encriptada")
            self._contrasena_plana = value
            self.contrasena_encriptada = make_password(value)
            print(f"[DEBUG] _contrasena_plana: {self._contrasena_plana}")
            print(f"[DEBUG] contrasena_encriptada: {self.contrasena_encriptada}")
    
    @property
    def get_contrasena_plana(self):
        """
        Devuelve la contraseña en texto plano si está disponible.
        Si no hay contraseña en texto plano, devuelve una cadena vacía.
        """
        print(f"[DEBUG] get_contrasena_plana llamado. _contrasena_plana: {self._contrasena_plana}")
        
        # Si _contrasena_plana es None o está vacío, devolvemos cadena vacía
        if not self._contrasena_plana:
            print("[DEBUG] No hay contraseña en texto plano")
            return ""
        
        # Verificar si la contraseña parece estar encriptada
        def es_contrasena_encriptada(contrasena):
            return (isinstance(contrasena, str) and 
                   (contrasena.startswith('bcrypt$') or 
                    contrasena.startswith('pbkdf2_sha256$') or
                    len(contrasena) > 50))
        
        # Si la contraseña parece estar encriptada
        if es_contrasena_encriptada(self._contrasena_plana):
            print("[DEBUG] Se detectó una contraseña encriptada en _contrasena_plana")
            
            # Si tenemos la contraseña encriptada y coincide con _contrasena_plana, 
            # significa que la contraseña original se perdió
            if self.contrasena_encriptada and self._contrasena_plana == self.contrasena_encriptada:
                print("[DEBUG] La contraseña encriptada coincide con _contrasena_plana")
                return ""
                
            # Si llegamos aquí, es posible que _contrasena_plana sea realmente la contraseña en texto plano
            # a pesar de que parece estar encriptada
            print("[DEBUG] Devolviendo _contrasena_plana a pesar de que parece encriptada")
            
            # Verificar si la contraseña es válida (solo letras y números, entre 8 y 30 caracteres)
            if (isinstance(self._contrasena_plana, str) and 
                8 <= len(self._contrasena_plana) <= 30 and
                all(c.isalnum() for c in self._contrasena_plana)):
                print("[DEBUG] La contraseña parece ser texto plano válido")
                return self._contrasena_plana
                
            print("[DEBUG] La contraseña no parece ser texto plano válido")
            return ""
            
        print("[DEBUG] Devolviendo contraseña en texto plano")
        return self._contrasena_plana

    def get_contrasena_encriptada(self):
        """Devuelve la contraseña encriptada"""
        if not self.contrasena_encriptada and self._contrasena_plana:
            self.contrasena_encriptada = make_password(self._contrasena_plana)
            self.save(update_fields=['contrasena_encriptada'])
        return self.contrasena_encriptada
        
    def verificar_contrasena(self, contrasena):
        """
        Verifica si la contraseña proporcionada coincide con la almacenada.
        
        Args:
            contrasena (str): Contraseña en texto plano a verificar
            
        Returns:
            bool: True si la contraseña es correcta, False en caso contrario
        """
        print("\n=== INICIO DE VERIFICACIÓN DE CONTRASEÑA ===")
        print(f"[DEBUG] Usuario: {self.usuario}")
        print(f"[DEBUG] Contraseña proporcionada: {contrasena}")
        print(f"[DEBUG] _contrasena_plana: {self._contrasena_plana}")
        print(f"[DEBUG] contrasena_encriptada: {self.contrasena_encriptada}")
        
        # Si hay una contraseña encriptada, la usamos para verificar
        if self.contrasena_encriptada:
            print("[DEBUG] Verificando con contraseña encriptada")
            from django.contrib.auth.hashers import check_password
            print(f"[DEBUG] Contraseña a verificar: {contrasena}")
            print(f"[DEBUG] Hash almacenado: {self.contrasena_encriptada}")
            
            # Verificar si la contraseña encriptada parece ser un hash válido
            if not (self.contrasena_encriptada.startswith('pbkdf2_sha256$') or 
                   self.contrasena_encriptada.startswith('bcrypt$') or
                   self.contrasena_encriptada.startswith('argon2')):
                print("[ERROR] El formato de la contraseña encriptada no es válido")
                print("=== FIN DE VERIFICACIÓN (ERROR) ===\n")
                return False
                
            es_valida = check_password(contrasena, self.contrasena_encriptada)
            print(f"[DEBUG] Resultado de check_password: {es_valida}")
            print("=== FIN DE VERIFICACIÓN ===\n")
            return es_valida
            
        # Si no hay contraseña encriptada pero hay una en texto plano, la comparamos directamente
        if self._contrasena_plana:
            print("[DEBUG] No hay contraseña encriptada, verificando con texto plano")
            es_valida = (contrasena == self._contrasena_plana)
            print(f"[DEBUG] Comparación directa: '{contrasena}' == '{self._contrasena_plana}'")
            print(f"[DEBUG] Resultado: {es_valida}")
            
            # Si la contraseña es correcta, la encriptamos para futuras verificaciones
            if es_valida:
                print("[DEBUG] Contraseña correcta, encriptando para futuras verificaciones")
                self.contrasena_encriptada = make_password(contrasena)
                self.save(update_fields=['contrasena_encriptada'])
                print("[DEBUG] Contraseña encriptada y guardada")
            
            print("=== FIN DE VERIFICACIÓN ===\n")
            return es_valida
            
        print("[DEBUG] No hay contraseña configurada para este usuario")
        print("=== FIN DE VERIFICACIÓN (SIN CONTRASEÑA) ===\n")
        return False

    def save(self, *args, **kwargs):
        print(f"[DEBUG] Iniciando save(). _contrasena_plana: {getattr(self, '_contrasena_plana', None)}")
        
        # Si es una actualización, obtener la instancia anterior
        if self.pk:
            try:
                old_instance = CredencialUsuario.objects.get(pk=self.pk)
                old_contrasena_plana = old_instance._contrasena_plana
            except CredencialUsuario.DoesNotExist:
                old_instance = None
                old_contrasena_plana = None
        else:
            old_instance = None
            old_contrasena_plana = None
        
        # Obtener la contraseña en texto plano si existe
        contrasena_plana = getattr(self, '_contrasena_plana', None)
        
        # Si es una nueva instancia o la contraseña ha cambiado
        if not self.pk or (contrasena_plana and contrasena_plana != getattr(old_instance, '_contrasena_plana', None)):
            print(f"[DEBUG] Nueva instancia o contraseña actualizada: {contrasena_plana}")
            
            # Si la contraseña parece estar encriptada, generar una nueva
            if (contrasena_plana and 
                isinstance(contrasena_plana, str) and 
                (contrasena_plana.startswith('bcrypt$') or 
                 contrasena_plana.startswith('pbkdf2_sha256$') or
                 len(contrasena_plana) > 50)):
                print("[ERROR] Se detectó una contraseña encriptada en _contrasena_plana")
                # Generar una nueva contraseña segura
                self.generar_contrasena(forzar=True)
                return
                
            # Si hay una contraseña en texto plano, generar el hash
            if contrasena_plana:
                print(f"[DEBUG] Generando hash para la contraseña: {contrasena_plana}")
                # Generar el hash solo para contrasena_encriptada
                self.contrasena_encriptada = make_password(contrasena_plana)
        
        print(f"[DEBUG] Guardando con _contrasena_plana: {getattr(self, '_contrasena_plana', None)}")
        print(f"[DEBUG] contrasena_encriptada: {self.contrasena_encriptada}")
            
        # Llamar al save del padre
        super().save(*args, **kwargs)
        
        # Asegurarse de que _contrasena_plana se guarde correctamente
        if contrasena_plana and self.pk:
            CredencialUsuario.objects.filter(pk=self.pk).update(_contrasena_plana=contrasena_plana)

    def verificar_contrasena(self, contrasena):
        """
        Verifica si la contraseña proporcionada coincide con la almacenada.
        
        Args:
            contrasena (str): Contraseña en texto plano a verificar
            
        Returns:
            bool: True si la contraseña es correcta, False en caso contrario
        """
        print("\n=== INICIO DE VERIFICACIÓN DE CONTRASEÑA ===")
        print(f"[DEBUG] Usuario: {self.usuario}")
        print(f"[DEBUG] Contraseña proporcionada: {contrasena}")
        print(f"[DEBUG] _contrasena_plana: {self._contrasena_plana}")
        print(f"[DEBUG] contrasena_encriptada: {self.contrasena_encriptada}")
        
        # Si hay una contraseña encriptada, la usamos para verificar
        if self.contrasena_encriptada:
            print("[DEBUG] Verificando con contraseña encriptada")
            from django.contrib.auth.hashers import check_password
            
            # Verificar si la contraseña encriptada parece ser un hash válido
            if not (self.contrasena_encriptada.startswith('pbkdf2_sha256$') or 
                   self.contrasena_encriptada.startswith('bcrypt$') or
                   self.contrasena_encriptada.startswith('argon2')):
                print("[ERROR] El formato de la contraseña encriptada no es válido")
                return False
                
            es_valida = check_password(contrasena, self.contrasena_encriptada)
            print(f"[DEBUG] Resultado de check_password: {es_valida}")
            
            # Si la verificación falla pero hay contraseña en texto plano, intentar con ella
            if not es_valida and self._contrasena_plana:
                print("[DEBUG] Verificación fallida, intentando con contraseña en texto plano")
                es_valida = (contrasena == self._contrasena_plana)
                print(f"[DEBUG] Resultado de comparación con texto plano: {es_valida}")
                
                # Si la contraseña en texto plano es correcta, actualizar el hash
                if es_valida:
                    print("[DEBUG] Actualizando hash de contraseña")
                    self.contrasena_encriptada = make_password(contrasena)
                    self.save(update_fields=['contrasena_encriptada'])
            
            print("=== FIN DE VERIFICACIÓN ===\n")
            return es_valida
            
        # Si no hay contraseña encriptada pero hay una en texto plano, la comparamos directamente
        if self._contrasena_plana:
            print("[DEBUG] No hay contraseña encriptada, verificando con texto plano")
            es_valida = (contrasena == self._contrasena_plana)
            
            # Si la contraseña es correcta, generamos el hash para futuras verificaciones
            if es_valida:
                print("[DEBUG] Contraseña correcta, generando hash")
                self.contrasena_encriptada = make_password(contrasena)
                self.save(update_fields=['contrasena_encriptada'])
            
            print(f"[DEBUG] Resultado de comparación con texto plano: {es_valida}")
            print("=== FIN DE VERIFICACIÓN ===\n")
            return es_valida
            
        print("[ERROR] No hay contraseña configurada para este usuario")
        print("=== FIN DE VERIFICACIÓN (ERROR) ===\n")
        return False

@receiver(pre_save, sender=CredencialUsuario)
def validar_credencial(sender, instance, **kwargs):
    """Validaciones adicionales antes de guardar una credencial"""
    # Verificar que el usuario (cedula) sea único
    if CredencialUsuario.objects.filter(usuario=instance.usuario).exclude(id=instance.id).exists():
        raise ValidationError('Ya existe una credencial con este usuario')
    
    # Solo encriptar la contraseña si no es una nueva generación
    if not instance.pk and not instance.contrasena.startswith('pbkdf2_sha256$'):
        instance.contrasena = make_password(instance.contrasena)