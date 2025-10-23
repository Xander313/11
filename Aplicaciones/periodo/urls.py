from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

# Función para aplicar login_required a las vistas basadas en funciones
def login_required_view(view_func):
    return login_required(view_func, login_url='agregarLogin')

urlpatterns = [
    # Rutas de gestión de períodos (requieren autenticación)
    path('periodo/agregarPeriodo/', login_required_view(views.agregarPeriodo), name='agregarPeriodo'),
    path('guardarPeriodo/', login_required_view(views.guardarPeriodo), name='guardarPeriodo'),
    path('editar-periodo/<int:id>/', login_required_view(views.editar_periodo), name='editar_periodo'),
    path('eliminar-periodo/<int:id>/', login_required_view(views.eliminar_periodo), name='eliminar_periodo'),
]
