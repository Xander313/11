from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views
from django.conf import settings
from django.conf.urls.static import static

# Función para aplicar login_required a las vistas basadas en funciones
def login_required_view(view_func):
    return login_required(view_func, login_url='agregarLogin')

urlpatterns = [
    # Rutas de configuración (requieren autenticación)
    path('configuracion/agregar_logo/', login_required_view(views.agregar_logo), name='agregar_logo'),
    path('configuracion-logo/', login_required_view(views.configurar_logo), name='configurar_logo'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)