from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.hashers import make_password
from .models import Grado, Paralelo, PadronElectoral, CredencialUsuario

@admin.register(CredencialUsuario)
class CredencialUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'get_padron_nombre', 'get_contrasena_plana_display', 'estado', 'fecha_generacion', 'acciones')
    search_fields = ('usuario', 'padron__nombre', 'padron__apellidos')
    list_filter = ('estado', 'fecha_generacion')
    readonly_fields = ('fecha_generacion', 'get_contrasena_plana_display', 'acciones')
    list_per_page = 20
    actions = ['regenerar_contrasena', 'desactivar_credenciales', 'activar_credenciales']
    
    def acciones(self, obj):
        return format_html(
            '<div class="actions">'
            '<a class="button" href="{}/change/"><i class="icon-edit"></i> Editar</a> '
            '<a class="button" href="{}/delete/" style="background-color: #ba2121;"><i class="icon-delete"></i> Eliminar</a>'
            '</div>',
            obj.id, obj.id
        )
    acciones.short_description = 'Acciones'
    acciones.allow_tags = True
    
    def regenerar_contrasena(self, request, queryset):
        for credencial in queryset:
            credencial.generar_contrasena()
            credencial.save()
        self.message_user(request, f'Se regeneraron {queryset.count()} contraseñas correctamente.')
    regenerar_contrasena.short_description = 'Regenerar contraseña seleccionadas'
    
    def desactivar_credenciales(self, request, queryset):
        actualizadas = queryset.update(estado='inactivo')
        self.message_user(request, f'Se desactivaron {actualizadas} credenciales correctamente.')
    desactivar_credenciales.short_description = 'Desactivar credenciales seleccionadas'
    
    def activar_credenciales(self, request, queryset):
        actualizadas = queryset.update(estado='activo')
        self.message_user(request, f'Se activaron {actualizadas} credenciales correctamente.')
    activar_credenciales.short_description = 'Activar credenciales seleccionadas'
    
    def get_readonly_fields(self, request, obj=None):
        """Hace que la contraseña sea de solo lectura si ya existe"""
        if obj and obj._contrasena_plana:
            return self.readonly_fields + ('contrasena',)
        return self.readonly_fields
    
    def get_form(self, request, obj=None, **kwargs):
        """Personaliza el formulario para manejar la contraseña"""
        form = super().get_form(request, obj, **kwargs)
        
        # Si el objeto ya tiene una contraseña, la hacemos de solo lectura
        if obj and obj._contrasena_plana:
            form.base_fields['contrasena'].help_text = 'Ya existe una contraseña generada. Para cambiarla, contacte a un administrador.'
        else:
            form.base_fields['contrasena'].help_text = 'Deje este campo en blanco para generar una contraseña automática'
            
        return form
    
    def get_contrasena_plana_display(self, obj):
        """Muestra la contraseña en texto plano solo si está disponible"""
        if obj._contrasena_plana:
            return '••••••••'  # Muestra 8 puntos como indicador de contraseña
        return "No generada"
    get_contrasena_plana_display.short_description = 'Contraseña'
    
    def get_padron_nombre(self, obj):
        return f"{obj.padron.nombre} {obj.padron.apellidos}"
    get_padron_nombre.short_description = 'Estudiante'
    get_padron_nombre.admin_order_field = 'padron__apellidos'
    
    def save_model(self, request, obj, form, change):
        """
        Asegura que la contraseña se guarde correctamente.
        Solo genera una nueva contraseña si no existe una previamente.
        """
        print(f"[DEBUG] Iniciando save_model. Cambios: {form.changed_data}")
        
        # Si es una edición, obtener el objeto actual de la base de datos
        if change and obj.pk:
            try:
                obj_actual = CredencialUsuario.objects.get(pk=obj.pk)
                # Si la contraseña no ha cambiado, mantener la existente
                if not form.changed_data or 'contrasena' not in form.changed_data:
                    print("[DEBUG] Manteniendo contraseña existente")
                    # Mantener la contraseña en texto plano si existe
                    if hasattr(obj_actual, '_contrasena_plana') and obj_actual._contrasena_plana:
                        # Verificar si la contraseña parece estar encriptada
                        contrasena_plana = obj_actual._contrasena_plana
                        if (isinstance(contrasena_plana, str) and 
                            (contrasena_plana.startswith('pbkdf2_sha256$') or 
                             contrasena_plana.startswith('bcrypt$') or
                             len(contrasena_plana) > 50)):
                            print("[DEBUG] Se detectó una contraseña encriptada en _contrasena_plana, generando una nueva")
                            obj.generar_contrasena()
                        else:
                            obj._contrasena_plana = contrasena_plana
                            print(f"[DEBUG] Contraseña en texto plano mantenida: {obj._contrasena_plana}")
                    else:
                        # Si no hay contraseña en texto plano, generar una nueva
                        print("[DEBUG] No hay contraseña existente, generando una nueva")
                        obj.generar_contrasena()
            except CredencialUsuario.DoesNotExist:
                pass
        
        # Si es nuevo o la contraseña ha cambiado, generar una nueva
        if not change or ('contrasena' in form.changed_data):
            print("[DEBUG] Generando nueva contraseña para objeto nuevo o contraseña modificada")
            obj.generar_contrasena()
        
        # Asegurarse de que tenemos una contraseña en texto plano
        if not obj._contrasena_plana or not isinstance(obj._contrasena_plana, str) or len(obj._contrasena_plana) > 50:
            print("[DEBUG] No se encontró una contraseña válida, generando una nueva")
            obj.generar_contrasena()
        
        # Guardar la contraseña en texto plano antes de llamar a save
        contrasena_plana = obj._contrasena_plana
        
        # Llamar al save del modelo para que se encargue de la encriptación
        super().save_model(request, obj, form, change)
        
        # Actualizar solo el campo _contrasena_plana con el valor en texto plano
        CredencialUsuario.objects.filter(pk=obj.pk).update(_contrasena_plana=contrasena_plana)
        print(f"[DEBUG] Contraseña guardada - Texto plano: {contrasena_plana}")

# Registro de los modelos restantes
admin.site.register(Grado)
admin.site.register(Paralelo)
admin.site.register(PadronElectoral)