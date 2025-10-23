from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views
from .views import GenerarCarnetPDF

app_name = 'votacion'

# Función para aplicar login_required a las vistas basadas en funciones
def login_required_view(view_func):
    return login_required(view_func, login_url='agregarLogin')

# Función para aplicar login_required a las vistas basadas en clases
def login_required_class_view(view_class):
    view_class.dispatch = login_required(view_class.dispatch, login_url='agregarLogin')
    return view_class

urlpatterns = [
    # Rutas de gestión de procesos electorales (requieren autenticación)
    path('iniciar/', login_required_view(views.iniciar_proceso), name='iniciar_proceso'),
    path('lista/', login_required_view(views.lista_procesos), name='lista_procesos'),
    path('editar/<int:proceso_id>/', login_required_view(views.editar_proceso), name='editar_proceso'),
    path('eliminar/<int:proceso_id>/', login_required_view(views.eliminar_proceso), name='eliminar_proceso'),

    # Obtener proceso activo (puede ser accedido sin autenticación para la papeleta)
    path('obtener-proceso-activo/', login_required_view(views.obtener_proceso_activo), name='obtener_proceso_activo'),

    # Papeleta de votación (accesible sin autenticación para votar)
    path('papeleta/<int:proceso_id>/', login_required_view(views.papeleta_votacion), name='papeleta_votacion'),

    # Registrar voto (accesible sin autenticación para permitir votar)
    path('registrar-voto/<int:proceso_id>/', login_required_view(views.registrar_voto), name='registrar_voto'),
    
    # Resultados de la votación (requiere autenticación)
    path('resultados/<int:proceso_id>/', login_required_view(views.resultados_votacion), name='resultados_votacion'),
    
    # Carnet de votación (requiere autenticación para generar/ver)
    path('carnet-votacion/', login_required_view(views.mostrar_carnet), name='mostrar_carnet'),
    
    # Descargar carnet en PDF (requiere autenticación)
    path('descargar-carnet/<int:carnet_id>/', 
         login_required_class_view(GenerarCarnetPDF).as_view(), 
         name='descargar_carnet'),
    
    # Verificar carnet (accesible sin autenticación para permitir la verificación)
    path('carnet/verificar/<str:codigo_verificacion>/', views.verificar_carnet, name='verificar_carnet'),
    path('carnet/datos-votante/<int:carnet_id>/', views.descargar_datos_votante, name='descargar_datos_votante'),
]