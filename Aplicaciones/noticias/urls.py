from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

app_name = 'noticias'

# Función para aplicar login_required a las vistas basadas en funciones
def login_required_view(view_func):
    return login_required(view_func, login_url='agregarLogin')

urlpatterns = [
    # URLs para noticias (requieren autenticación)
    path('listar_noticias/', login_required_view(views.listar_noticias), name='listar_noticias'),
    path('agregar/', login_required_view(views.agregar_noticia), name='agregar_noticia'),
    path('editar/<int:noticia_id>/', login_required_view(views.editar_noticia), name='editar_noticia'),
    path('eliminar/<int:noticia_id>/', login_required_view(views.eliminar_noticia), name='eliminar_noticia'),
    path('ver/<int:noticia_id>/', login_required_view(views.ver_noticia), name='ver_noticia'),
    path('eliminar-imagen/<int:imagen_id>/', login_required_view(views.eliminar_imagen_adicional), name='eliminar_imagen_adicional'),
    
    # URLs para categorías (requieren autenticación)
    path('categorias/', login_required_view(views.listar_categorias), name='listar_categorias'),
    path('categorias/agregar/', login_required_view(views.agregar_editar_categoria), name='agregar_categoria'),
    path('categorias/editar/<int:categoria_id>/', login_required_view(views.agregar_editar_categoria), name='editar_categoria'),
    path('categorias/eliminar/<int:categoria_id>/', login_required_view(views.eliminar_categoria), name='eliminar_categoria'),
]
