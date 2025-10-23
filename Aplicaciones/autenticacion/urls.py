from django.urls import path
from . import views

urlpatterns = [
    path('login/agregarLogin/', views.agregarLogin, name='agregarLogin'),
]
