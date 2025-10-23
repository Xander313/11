from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views
from .views import descargar_backup_sqlite

# Función para aplicar login_required a las vistas basadas en funciones
def login_required_view(view_func):
    return login_required(view_func, login_url='agregarLogin')

urlpatterns = [
    # Rutas de resultados (requieren autenticación)
    path('proceso/<int:proceso_id>/', login_required_view(views.resultados_votacion), name='resultados_votacion'),
    path('proceso/<int:proceso_id>/reporte_pdf/', login_required_view(views.generar_reporte_pdf), name='generar_reporte_pdf'),
    path('lista/', login_required_view(views.lista_resultados), name='lista_resultados'),

    #Descargar backup
    path('descargar_backup/', descargar_backup_sqlite, name='descargar_backup'),

    
]
