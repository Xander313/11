from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from Aplicaciones.padron.models import CredencialUsuario
from Aplicaciones.noticias.models import Noticia, Categoria
from django.contrib.auth.hashers import check_password
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

# Create your views here.
def index(request):
    if request.user.is_authenticated:
        # Redirigir a la página de inicio de sesión del padrón
        return render(request, 'index.html')
    return render(request, 'index.html')

@csrf_exempt
@require_http_methods(["POST"])
def login_padron(request):
    # Log the incoming request data for debugging
    print("\n=== INICIO DE SOLICITUD DE INICIO DE SESIÓN ===")
    print(f"Método: {request.method}")
    print(f"POST data: {request.POST}")
    
    # Verificar el token CSRF
    if not request.META.get('CSRF_COOKIE'):
        print("Error: No se encontró el token CSRF en las cookies")
        return JsonResponse({
            'success': False,
            'message': 'Error de seguridad. Por favor, recargue la página e intente nuevamente.'
        }, status=403)
    
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '').strip()
    
    if not username or not password:
        return JsonResponse({
            'success': False,
            'message': 'Por favor ingrese su usuario y contraseña'
        }, status=400)
    
    # 1. Primero intentar autenticar como usuario del sistema
    from django.contrib.auth import authenticate, login as auth_login
    from Aplicaciones.usuarios.models import Usuarios
    
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        # Usuario del sistema autenticado correctamente
        if user.is_active:
            auth_login(request, user)
            print(f"Usuario del sistema {username} autenticado correctamente")
            
            # Verificar si el usuario es del padrón (tiene un padrón asociado)
            if hasattr(user, 'padron'):
                # Si es del padrón, redirigir a la papeleta
                from Aplicaciones.votacion.models import ProcesoElectoral
                try:
                    proceso_activo = ProcesoElectoral.objects.get(estado='activo')
                    redirect_url = f'/votacion/papeleta/{proceso_activo.id}/'
                    return JsonResponse({
                        'success': True,
                        'redirect_url': redirect_url,
                        'message': 'Redirigiendo a la papeleta de votación...'
                    })
                except ProcesoElectoral.DoesNotExist:
                    pass  # Continuar con la redirección al dashboard
            
            # Para usuarios del sistema que no son del padrón, redirigir al dashboard
            return JsonResponse({
                'success': True,
                'redirect_url': '/rol/dashboard/',  # Redirigir al dashboard
                'message': 'Inicio de sesión exitoso'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Su cuenta está desactivada'
            }, status=400)
    
    # 2. Si no es un usuario del sistema, intentar autenticar como padrón
    try:
        from Aplicaciones.padron.models import CredencialUsuario
        print(f"Buscando credencial para el usuario: {username}")
        
        try:
            credencial = CredencialUsuario.objects.get(usuario=username)
            print(f"Credencial encontrada: {credencial}")
            
            # Verificar si la cuenta está activa
            if credencial.estado != 'activo':
                print(f"Error: La cuenta del usuario {username} no está activa. Estado actual: {credencial.estado}")
                return JsonResponse({
                    'success': False,
                    'message': 'Su cuenta no está activa. Por favor, contacte al administrador.'
                }, status=400)
            
            # Verificar la contraseña del padrón
            if not credencial.verificar_contrasena(password):
                print(f"[ERROR] La verificación de contraseña falló para el usuario {username}")
                return JsonResponse({
                    'success': False,
                    'message': 'Cédula o contraseña incorrectos'
                }, status=400)
            
            # Verificar si ya votó
            if hasattr(credencial.padron, 'voto') and credencial.padron.voto:
                print(f"Usuario {username} intentó votar nuevamente - Voto ya emitido")
                return JsonResponse({
                    'success': False,
                    'message': 'Usted ya ha emitido su voto para este proceso electoral. No puede votar nuevamente.',
                    'voto_ya_emitido': True
                }, status=400)
            
            # Iniciar sesión para el padrón
            request.session['padron_autenticado'] = True
            request.session['padron_id'] = credencial.padron.id
            
            # Obtener el proceso electoral activo
            from Aplicaciones.votacion.models import ProcesoElectoral
            try:
                proceso_activo = ProcesoElectoral.objects.get(estado='activo')
                redirect_url = f'/votacion/papeleta/{proceso_activo.id}/'
            except ProcesoElectoral.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'No hay un proceso electoral activo en este momento.'
                }, status=400)
            
            return JsonResponse({
                'success': True,
                'redirect_url': redirect_url,
                'message': 'Autenticación exitosa para votación'
            })
            
        except CredencialUsuario.DoesNotExist:
            print(f"Error: No se encontró el usuario {username} en el padrón")
            return JsonResponse({
                'success': False,
                'message': 'Usuario o contraseña incorrectos'
            }, status=400)
            
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': 'Ocurrió un error al procesar la solicitud',
            'error': str(e)
        }, status=500)



@login_required
def logout_padron(request):
    auth_logout(request)
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('administracion:index')

@login_required
@login_required(login_url='agregarLogin')
def dashboard(request):
    return render(request, 'administracion/dashboard.html')

def plantilla(request):
    return render(request, 'administracion/plantilla.html')

def mision_vision(request):
    return render(request, 'administracion/mision_vision.html')

def nosotros(request):
    return render(request, 'administracion/nosotros.html')

def docentes(request):
    return render(request, 'administracion/docentes.html')

def docentes_nuevo(request):
    return render(request, 'administracion/docentes-nuevo.html')

def noticias(request):
    # Obtener noticias destacadas
    noticias_destacadas = Noticia.objects.filter(
        destacada=True, 
        estado='publicado'
    ).order_by('-fecha_publicacion')[:3]
    
    # Obtener últimas noticias (no destacadas)
    ultimas_noticias = Noticia.objects.filter(
        estado='publicado'
    ).exclude(
        id__in=noticias_destacadas.values_list('id', flat=True)
    ).order_by('-fecha_publicacion')[:6]
    
    # Obtener todas las categorías para el filtro
    categorias = Categoria.objects.filter(activo=True)
    
    context = {
        'noticias_destacadas': noticias_destacadas,
        'ultimas_noticias': ultimas_noticias,
        'categorias': categorias,
    }
    
    return render(request, 'administracion/noticias.html', context)
