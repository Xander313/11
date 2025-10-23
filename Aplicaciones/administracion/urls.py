from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.csrf import csrf_exempt

app_name = 'administracion'

# Función para aplicar login_required a las vistas basadas en funciones
def login_required_view(view_func):
    return login_required(view_func, login_url='agregarLogin')

urlpatterns = [
    # Páginas informativas (accesibles sin autenticación)
    path('', views.index, name='index'),
    path('mision-vision/', views.mision_vision, name='mision_vision'),
    path('nosotros/', views.nosotros, name='nosotros'),
    
    # Solo el dashboard requiere autenticación
    path('dashboard/', login_required_view(views.dashboard), name='dashboard'),
    
    # Otras rutas (accesibles sin autenticación)
    path('administracion/plantilla/', views.plantilla, name='administracion/plantilla'),
    path('docentes/', views.docentes, name='docentes'),
    path('docentes-nuevo/', views.docentes_nuevo, name='docentes-nuevo'),
    path('noticias/', views.noticias, name='noticias'),
    
    # Autenticación (sin protección de login_required)
    path('login/', csrf_exempt(views.login_padron), name='login_padron'),
    path('logout/', views.logout_padron, name='logout_padron'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)