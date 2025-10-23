from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import Periodo
from datetime import datetime, date
from django.contrib.auth.decorators import login_required

# Función para actualizar el estado de un período según las fechas
def actualizar_estado_periodo(periodo):
    hoy = date.today()
    if hoy < periodo.fecha_inicio:
        periodo.estado = 'Inactivo'
    elif periodo.fecha_inicio <= hoy <= periodo.fecha_fin:
        periodo.estado = 'Activo'
    else:
        periodo.estado = 'Finalizado'
    periodo.save()
    return periodo

# Vista para mostrar la página de periodos con el formulario y la tabla
@login_required
def agregarPeriodo(request):
    # Obtener todos los períodos ordenados por fecha de inicio (más recientes primero)
    periodos = Periodo.objects.all().order_by('-fecha_inicio')
    
    # Actualizar el estado de cada período según las fechas
    for periodo in periodos:
        actualizar_estado_periodo(periodo)
    
    return render(request, 'periodo/agregarPeriodo.html', {'periodos': periodos})


# Vista para guardar un nuevo periodo
@login_required
def guardarPeriodo(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')

        if fecha_inicio >= fecha_fin:
            messages.error(request, 'La fecha de fin debe ser posterior a la fecha de inicio.')
            return redirect('agregarPeriodo')

        # Convertir las cadenas de fecha a objetos date
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        hoy = date.today()
        
        # Determinar el estado inicial
        estado = 'Inactivo'
        if fecha_inicio_dt <= hoy <= fecha_fin_dt:
            estado = 'Activo'
        elif hoy > fecha_fin_dt:
            estado = 'Finalizado'
            
        periodo = Periodo(
            nombre=nombre,
            fecha_inicio=fecha_inicio_dt,
            fecha_fin=fecha_fin_dt,
            estado=estado
        )
        periodo.save()
        messages.success(request, 'Periodo académico agregado correctamente.')
    return redirect('agregarPeriodo')


# Vista para editar un periodo existente
def editar_periodo(request, id):
    periodo = get_object_or_404(Periodo, id=id)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')

        if fecha_inicio >= fecha_fin:
            messages.error(request, 'La fecha de fin debe ser posterior a la fecha de inicio.')
            return redirect('agregarPeriodo')

        # Convertir las cadenas de fecha a objetos date
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        hoy = date.today()
        
        # Actualizar los datos del período
        periodo.nombre = nombre
        periodo.fecha_inicio = fecha_inicio_dt
        periodo.fecha_fin = fecha_fin_dt
        
        # Actualizar el estado según las fechas
        if hoy < fecha_inicio_dt:
            periodo.estado = 'Inactivo'
        elif fecha_inicio_dt <= hoy <= fecha_fin_dt:
            periodo.estado = 'Activo'
        else:
            periodo.estado = 'Finalizado'
            
        periodo.save()

        messages.success(request, 'Periodo académico actualizado correctamente.')
        return redirect('agregarPeriodo')


# Vista para eliminar un periodo
def eliminar_periodo(request, id):
    periodo = get_object_or_404(Periodo, id=id)
    periodo.delete()
    messages.success(request, f'Periodo académico {periodo.nombre} eliminado correctamente.')
    return redirect('agregarPeriodo')
