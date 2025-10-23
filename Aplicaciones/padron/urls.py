from django.urls import path
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from . import views
from .views import (
    GradoListView, agregar_grado, editar_grado, eliminar_grado,
    ParaleloListView, agregar_paralelo, editar_paralelo, eliminar_paralelo
)

# Función para aplicar login_required a las vistas basadas en funciones
def login_required_view(view_func):
    return login_required(view_func, login_url='agregarLogin')

# Función para aplicar login_required a las vistas basadas en clases
def login_required_class_view(view_class):
    view_class.dispatch = login_required(view_class.dispatch, login_url='agregarLogin')
    return view_class

urlpatterns = [
    # URLs para Grados
    path('grados/', GradoListView.as_view(), name='listar_grados'),
    path('grados/agregar/', login_required_view(agregar_grado), name='agregar_grado'),
    path('grados/editar/<int:id>/', login_required_view(editar_grado), name='editar_grado'),
    path('grados/eliminar/<int:id>/', login_required_view(eliminar_grado), name='eliminar_grado'),
    
    # URLs para Paralelos
    path('paralelos/', ParaleloListView.as_view(), name='listar_paralelos'),
    path('paralelos/agregar/', login_required_view(agregar_paralelo), name='agregar_paralelo'),
    path('paralelos/editar/<int:id>/', login_required_view(editar_paralelo), name='editar_paralelo'),
    path('paralelos/eliminar/<int:id>/', login_required_view(eliminar_paralelo), name='eliminar_paralelo'),
    
    # URLs para el Padrón Electoral
    path('padron/', login_required_view(views.gestion_padron), name='gestion_padron'),
    path('padron/agregar/', login_required_view(views.agregar_estudiante), name='agregar_estudiante'),
    path('padron/editar/<int:estudiante_id>/', login_required_view(views.editar_estudiante), name='editar_estudiante'),
    path('padron/eliminar/<int:estudiante_id>/', login_required_view(views.eliminar_estudiante), name='eliminar_estudiante'),
    path('padron/cargar-paralelos/', login_required_view(views.cargar_paralelos), name='cargar_paralelos'),
    path('padron/exportar-excel/', login_required_view(views.exportar_padron_excel), name='exportar_padron_excel'),
    path('padron/importar-excel/', login_required_view(views.importar_padron_excel), name='importar_padron_excel'),
    path('padron/estadisticas/', login_required_view(views.estadisticas_padron), name='estadisticas_padron'),
    path('padron/eliminar-todo/', login_required_view(views.eliminar_todo_el_padron), name='eliminar_todo_el_padron'),
    path('padron/generar-credenciales/', login_required_view(views.generar_credenciales), name='generar_credenciales'),
    path('padron/exportar-credenciales-pdf/', login_required_view(views.exportar_credenciales_pdf), name='exportar_credenciales_pdf'),
    path('padron/enviar-credenciales/', login_required_view(views.enviar_credenciales), name='enviar_credenciales'),
]
