from django.shortcuts import render, redirect
from .models import Roles, Usuarios
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.conf import settings

from Aplicaciones.padron.models import PadronElectoral
from Aplicaciones.votacion.models import ProcesoElectoral, Voto, Candidato

import random
import string
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
import json
# Create your views here.




from django.contrib.auth.decorators import login_required

@login_required(login_url='agregarLogin')
def dashboard(request):
    # Verificar si el usuario necesita cambiar su contraseña
    if request.user.primer_inicio:
        # Forzar la actualización de la sesión
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, request.user)
        
        # Agregar contexto para mostrar el modal (aunque será manejado por la redirección)
        context = {'mostrar_modal': True}
        return render(request, 'rol/dashboard.html', context)
        
    # Datos existentes
    total_usuarios = Usuarios.objects.count()
    total_estudiantes = PadronElectoral.objects.count()
    total_votantes = Voto.objects.values('votante').distinct().count()
    
    # Datos para el gráfico de estudiantes por grado
    from Aplicaciones.padron.models import Grado
    from django.db.models import Count
    
    # Obtener grados con su cantidad de estudiantes
    grados_con_estudiantes = Grado.objects.annotate(
        num_estudiantes=Count('padronelectoral')
    ).filter(num_estudiantes__gt=0).order_by('nombre')
    
    # Preparar datos para el gráfico
    grados_labels = [grado.nombre for grado in grados_con_estudiantes]
    estudiantes_por_grado = [grado.num_estudiantes for grado in grados_con_estudiantes]
    
    # Convertir a JSON para JavaScript
    grados_labels_json = json.dumps(grados_labels)
    estudiantes_por_grado_json = json.dumps(estudiantes_por_grado)
    
    # Obtener el proceso electoral activo (asumiendo que el estado 'activo' o 'en curso')
    proceso_activo = ProcesoElectoral.objects.filter(estado='activo').first()
    resultados = []
    
    if proceso_activo:
        # Get the periodo from the active electoral process
        periodo_activo = proceso_activo.periodo
        # Get candidates for the active periodo
        candidatos = Candidato.objects.filter(periodo=proceso_activo.periodo)
        # Contar votos por candidato
        for candidato in candidatos:
            votos = Voto.objects.filter(lista=candidato.lista).count()
            resultados.append({
                'candidato': candidato,
                'votos': votos
            })
    
    # Datos del estudiante (si está logueado y es un estudiante)
    estudiante = None
    if request.user.is_authenticated and hasattr(request.user, 'padronelectoral'):
        estudiante = request.user.padronelectoral
    
    if resultados:
        # Convertir resultados a formato JSON
        resultados_data = []
        for r in resultados:
            resultados_data.append({
                'candidato': r['candidato'].nombre_candidato,
                'votos': r['votos']
            })
        resultados_json = json.dumps(resultados_data)
    else:
        resultados_json = '[]'

    context = {
        'total_usuarios': total_usuarios,
        'total_estudiantes': total_estudiantes,
        'total_votantes': total_votantes,
        'resultados': resultados,
        'estudiante': estudiante,
        'resultados_json': resultados_json,
        'mostrar_modal': request.user.primer_inicio,
        'grados_labels': grados_labels_json,
        'estudiantes_por_grado': estudiantes_por_grado_json
    }
    return render(request, 'rol/dashboard.html', context)

#CREAMOS LAS VIEWS PARA LOS ROLES


@login_required(login_url='agregarLogin')
def agregarrol(request):
    roles = Roles.objects.all()
    cantidad_roles = roles.count()
    return render(request, 'rol/agregarrol.html', {'roles': roles, 'cantidad_roles': cantidad_roles})

@login_required(login_url='agregarLogin')
def guardarrol(request):
    nombre_rol=request.POST['nombre_rol']
    descripcion=request.POST['descripcion']
    Roles.objects.create(nombre_rol=nombre_rol, descripcion=descripcion)
    return redirect('agregarrol')

@login_required(login_url='agregarLogin')
def listarroles(request):
    roles = Roles.objects.all()
    return render(request, 'rol/agregarrol.html', {'roles': roles})

@login_required(login_url='agregarLogin')
def editar_rol(request, id):
    rol = get_object_or_404(Roles, id=id)
    
    if request.method == "POST":
        nombre_rol = request.POST.get("nombre_rol")
        descripcion = request.POST.get("descripcion", "")

        if nombre_rol:
            rol.nombre_rol = nombre_rol
            rol.descripcion = descripcion
            rol.save()
            messages.success(request, "Rol actualizado correctamente.")
            return redirect('listarroles')
        else:
            messages.error(request, "El nombre del rol es obligatorio.")

    return render(request, 'editar_rol.html', {'rol': rol})

@login_required(login_url='agregarLogin')
def actualizarrol(request, id):
    rol = Roles.objects.get(id=id)
    rol.nombre_rol = request.POST['nombre_rol']
    rol.descripcion = request.POST['descripcion']
    rol.save()
    return redirect('listarroles')

@login_required(login_url='agregarLogin')
def eliminarrol(request, id):
    rol = Roles.objects.get(id=id)
    rol.delete()
    return redirect('listarroles')

#CREAMOS LAS VIEWS PARA LOS USUARIOS
# Vista para mostrar la página con la tabla y el modal
@login_required(login_url='agregarLogin')
def agregarUsuario(request):
    roles = Roles.objects.all()
    usuarios = Usuarios.objects.all()  # Obtener todos los usuarios para la tabla
    return render(request, 'usuarios/agregarUsuario.html', {'roles': roles, 'usuarios': usuarios})

def generar_contraseña_aleatoria(longitud=8):
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choice(caracteres) for _ in range(longitud))

@login_required(login_url='agregarLogin')
def guardarUsuario(request):
    if request.method == 'POST':
        print('Método POST recibido')
        print('POST data:', request.POST)
        print('FILES:', request.FILES)
        
        try:
            # Validar que todos los campos requeridos estén presentes
            required_fields = ['cedula', 'nombre', 'email', 'id_rol']
            for field in required_fields:
                if field not in request.POST or not request.POST[field].strip():
                    messages.error(request, f'El campo {field} es obligatorio')
                    return redirect('agregarUsuario')
            
            # Obtener datos del formulario
            cedula = request.POST['cedula'].strip()
            nombre = request.POST['nombre'].strip()
            apellido = request.POST.get('apellido', '').strip()
            email = request.POST['email'].strip()
            id_rol = request.POST['id_rol']
            activo = request.POST.get('activo', 'off') == 'on'
            imagen = request.FILES.get('imagen')
            
            print('Datos extraídos correctamente:')
            print(f'Cédula: {cedula}')
            print(f'Nombre: {nombre}')
            print(f'Apellido: {apellido}')
            print(f'Email: {email}')
            print(f'Rol ID: {id_rol}')
            print(f'Activo: {activo}')
            print(f'Imagen: {imagen}')

            # Verificar si la cédula (username) ya está registrada
            if Usuarios.objects.filter(username=cedula).exists():
                messages.error(request, 'La cédula ya está registrada como nombre de usuario.')
                return redirect('agregarUsuario')
                
            # Verificar si el correo ya está registrado
            if Usuarios.objects.filter(email=email).exists():
                messages.error(request, 'El correo electrónico ya está registrado.')
                return redirect('agregarUsuario')

            # Generar contraseña aleatoria
            password_aleatoria = generar_contraseña_aleatoria()
            print(f'Contraseña generada: {password_aleatoria}')

            try:
                # Crear usuario usando create_user para manejar correctamente la contraseña
                usuario = Usuarios.objects.create_user(
                    username=cedula,
                    email=email,
                    password=password_aleatoria,
                    nombre=nombre,  # Usando el campo personalizado
                    apellido=apellido,  # Usando el campo personalizado
                    id_rol_id=id_rol,
                    activo=activo,
                    plain_password=password_aleatoria,
                    primer_inicio=True  # Establecer primer_inicio como True para forzar cambio de contraseña
                )
                
                # Si hay una imagen, guardarla después de crear el usuario
                if imagen:
                    usuario.imagen = imagen
                    usuario.save()
                    
                print('Usuario creado y guardado exitosamente')
                
            except Exception as e:
                print(f'Error al guardar el usuario: {str(e)}')
                messages.error(request, f'Error al guardar el usuario: {str(e)}')
                return redirect('agregarUsuario')
            
        except KeyError as e:
            error_msg = f'Error: Campo faltante en el formulario - {str(e)}'
            print(error_msg)
            messages.error(request, error_msg)
            return redirect('agregarUsuario')
            
        except Exception as e:
            error_msg = f'Error inesperado: {str(e)}'
            print(error_msg)
            import traceback
            print(traceback.format_exc())  # Imprimir el traceback completo
            messages.error(request, 'Ocurrió un error al procesar la solicitud. Por favor, intente nuevamente.')
            return redirect('agregarUsuario')

        # Enviar la contraseña por correo electrónico
        try:
            send_mail(
                'Credenciales de acceso al Sistema de Votación de la Unidad Educativa Riobamba',
                f'Hola {nombre} {apellido},\n\nTus credenciales de acceso al sistema son las siguientes:\n\nUsuario (Cédula): {cedula}\nContraseña: {password_aleatoria}\n\nPor seguridad, te recomendamos cambiar tu contraseña después de iniciar sesión por primera vez.\n\nAtentamente,\nConsejo Electoral - Unidad Educativa Riobamba',
                settings.DEFAULT_FROM_EMAIL,  # Usar el remitente configurado en settings.py
                [email],
                fail_silently=True,  # Cambiado a True para que no falle si hay error en el envío
            )
            messages.success(request, 'Usuario creado exitosamente y credenciales enviadas por correo.')
        except Exception as e:
            error_msg = f'Usuario creado, pero ocurrió un error al enviar el correo: {str(e)}'
            print(error_msg)
            messages.warning(request, error_msg)
            messages.info(request, f'La contraseña generada es: {password_aleatoria}. Por favor, anótela y guárdela en un lugar seguro.')
            return redirect('agregarUsuario')

        messages.success(request, 'Usuario agregado con éxito y contraseña enviada al correo.')
        return redirect('agregarUsuario')

    roles = Roles.objects.all()
    return render(request, 'usuarios/agregarUsuario.html', {'roles': roles})


@login_required(login_url='agregarLogin')
def listarUsuarios(request):
    roles = Roles.objects.all()
    usuarios = Usuarios.objects.all()  # Obtiene todos los usuarios

    return render(request, 'usuarios/agregarUsuario.html', {'usuarios': usuarios, 'roles': roles})


@login_required(login_url='agregarLogin')
def editarUsuario(request, usuario_id):
    usuario = get_object_or_404(Usuarios, id=usuario_id)
    
    if request.method == 'POST':
        try:
            # Actualizar campos personalizados
            usuario.nombre = request.POST.get('nombre')
            usuario.apellido = request.POST.get('apellido', '')
            
            # Actualizar campos estándar de Django
            usuario.first_name = request.POST.get('nombre', '')
            usuario.last_name = request.POST.get('apellido', '')
            
            # Actualizar el resto de campos
            usuario.email = request.POST.get('email')
            usuario.username = request.POST.get('username')
            
            # Actualizar contraseña si se proporciona
            password = request.POST.get('password')
            if password:
                usuario.set_password(password)
                
            usuario.id_rol_id = request.POST.get('id_rol')
            usuario.activo = request.POST.get('activo', 'off') == 'on'
            
            # Actualizar imagen si se proporciona
            if 'imagen' in request.FILES:
                usuario.imagen = request.FILES['imagen']
                
            usuario.save()
            messages.success(request, 'Usuario actualizado con éxito.')
        except Exception as e:
            messages.error(request, f'Error al actualizar el usuario: {str(e)}')
        return redirect('agregarUsuario')
    
    usuarios = Usuarios.objects.all()
    roles = Roles.objects.all()
    return render(request, 'usuarios/agregarUsuario.html', {
        'usuarios': usuarios,
        'roles': roles,
        'usuario': usuario
    })


@login_required(login_url='agregarLogin')
def eliminarUsuario(request, id):
    # Obtener al usuario con el id proporcionado
    usuario = get_object_or_404(Usuarios, id=id)

    # Eliminar el usuario definitivamente
    usuario.delete()
    messages.success(request, "Usuario eliminado con éxito.")

    # Redirigir a la vista donde se listan/agregan usuarios
    return redirect('agregarUsuario')

#LOGIN

from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import update_session_auth_hash

class CambioContrasena(PasswordChangeView):
    template_name = 'usuarios/password_change_form.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            self.request.user.primer_inicio = False
            self.request.user.save()
            
            # Si es una petición AJAX, devolver respuesta JSON
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Contraseña cambiada exitosamente.'
                })
                
            messages.success(self.request, 'Contraseña cambiada exitosamente. Ya no estás en primer inicio.')
            return response
            
        except Exception as e:
            error_message = f'Error al cambiar la contraseña: {str(e)}'
            
            # Si es una petición AJAX, devolver error en JSON
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': {'__all__': [error_message]}
                }, status=400)
                
            messages.error(self.request, error_message)
            return super().form_invalid(form)

    def form_invalid(self, form):
        error_message = 'Por favor, corrige los errores en el formulario.'
        
        # Si es una petición AJAX, devolver errores de validación en JSON
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
                
            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)
            
        messages.error(self.request, error_message)
        return super().form_invalid(form)
        
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
