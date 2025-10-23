from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

# Función para aplicar login_required a las vistas basadas en funciones
def login_required_view(view_func):
    return login_required(view_func, login_url='agregarLogin')

urlpatterns = [
    # Búsquedas y verificaciones
    path('buscar_nombre_por_cedula/', login_required_view(views.buscar_nombre_por_cedula), name='buscar_nombre_por_cedula'),
    path('verificar_estudiante/', login_required_view(views.verificar_estudiante_lista), name='verificar_estudiante_lista'),
    path('buscar_cedula_por_nombre/', login_required_view(views.buscar_cedula_por_nombre), name='buscar_cedula_por_nombre'),
    
    # Rutas de Listas
    path('listas/', login_required_view(views.listar_listas), name='listar_listas'),
    path('lista/nueva/', login_required_view(views.agregar_lista), name='nueva_lista'),
    path('lista/editar/<int:lista_id>/', login_required_view(views.editar_lista), name='editar_lista'),
    path('lista/eliminar/<int:lista_id>/', login_required_view(views.eliminar_lista), name='eliminar_lista'),

    # Rutas de Cargos
    path('cargo/', login_required_view(views.listar_cargos), name='listar_cargos'),
    path('cargo/nuevo/', login_required_view(views.agregar_cargo), name='nuevo_cargo'),
    path('cargo/editar/<int:cargo_id>/', login_required_view(views.agregar_cargo), name='editar_cargo'),
    path('cargo/eliminar/<int:cargo_id>/', login_required_view(views.eliminar_cargo), name='eliminar_cargo'),

    # Rutas de Candidatos
    path('candidatos/', login_required_view(views.listar_candidatos), name='listar_candidatos'),
    path('candidatos/agregar/', login_required_view(views.agregar_candidato), name='agregar_candidato'),
    path('candidatos/editar/<int:candidato_id>/', login_required_view(views.editar_candidato), name='editar_candidato'),
    path('candidatos/eliminar/<int:candidato_id>/', login_required_view(views.eliminar_candidato), name='eliminar_candidato'),
    
    # Limpieza de listas huérfanas
    path('listas/limpiar/', login_required_view(views.limpiar_listas_sin_candidatos), name='limpiar_listas_sin_candidatos'),
]