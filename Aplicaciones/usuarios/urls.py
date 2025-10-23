from django.urls import path
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import CambioContrasena, dashboard, editar_rol, eliminarrol, agregarUsuario, guardarUsuario, listarUsuarios, eliminarUsuario, editarUsuario

# Función para aplicar login_required a todas las vistas
def login_required_decorator(func):
    """Aplica login_required a una vista, excepto si ya lo tiene"""
    decorator = login_required(login_url='agregarLogin')
    if hasattr(func, 'view_class'):  # Para class-based views
        func.view_class = type(
            func.view_class.__name__,
            (func.view_class,),
            {'dispatch': decorator(func.view_class.dispatch)}
        )
        return func
    else:  # Para function-based views
        return decorator(func)

# Lista de vistas que necesitan protección
urlpatterns = [
    path('rol/dashboard/', login_required(dashboard), name='dashboard'),
    
    # Vistas de roles
    path('rol/agregarrol/', login_required(views.agregarrol), name='agregarrol'),
    path('rol/guardarrol/', login_required(views.guardarrol), name='guardarrol'),
    path('rol/listarroles/', login_required(views.listarroles), name='listarroles'),
    path('editar_rol/<int:id>/', login_required(views.editar_rol), name='editar_rol'),
    path('actualizarrol/<int:id>/', login_required(views.actualizarrol), name='actualizarrol'),
    path('eliminarrol/<int:id>/', login_required(views.eliminarrol), name='eliminarrol'),
    
    # Vistas de usuarios
    path('usuarios/agregarUsuario/', login_required(views.agregarUsuario), name='agregarUsuario'),
    path('usuarios/guardarUsuario/', login_required(views.guardarUsuario), name='guardarUsuario'),
    path('usuarios/listarUsuarios/', login_required(views.listarUsuarios), name='listarUsuarios'),
    path('editarUsuario/<int:usuario_id>/', login_required(editarUsuario), name='editarUsuario'),
    path('eliminarUsuario/<int:id>/', login_required(views.eliminarUsuario), name='eliminarUsuario'),
    
    # Cambio de contraseña
    path('cambiar-contrasena/', login_required(CambioContrasena.as_view()), name='cambiar_contrasena'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Configuración para redirigir a la página de login si no está autenticado
login_url = 'agregarLogin'
login_redirect_url = 'agregarLogin'