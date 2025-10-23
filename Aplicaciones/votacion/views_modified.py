from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count
from django.urls import reverse
from django.http import JsonResponse
from .models import ProcesoElectoral, Voto
from Aplicaciones.periodo.models import Periodo
from Aplicaciones.elecciones.models import Lista, Candidato
from Aplicaciones.padron.models import PadronElectoral
import hashlib

def generar_hash_voto(proceso_id, votante_id, timestamp):
    texto = f"{proceso_id}-{votante_id}-{timestamp}"
    return hashlib.sha256(texto.encode()).hexdigest()

def iniciar_proceso(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        periodo_id = request.POST.get('periodo')
        fecha = request.POST.get('fecha')
        hora_inicio = request.POST.get('hora_inicio')
        hora_fin = request.POST.get('hora_fin')
        descripcion = request.POST.get('descripcion')

        try:
            periodo = get_object_or_404(Periodo, id=periodo_id)
            
            proceso = ProcesoElectoral(
                nombre=nombre,
                periodo=periodo,
                fecha=fecha,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                descripcion=descripcion
            )
            proceso.save()
            
            messages.success(request, 'Proceso electoral creado exitosamente')
            return redirect('votacion:lista_procesos')
        except Exception as e:
            messages.error(request, f'Error al crear el proceso: {str(e)}')
            return redirect('votacion:iniciar_proceso')

    # Obtener los períodos activos
    periodos = Periodo.objects.filter(estado='activo')
    return render(request, 'votacion/proceso/iniciar.html', {'periodos': periodos})

def lista_procesos(request):
    procesos = ProcesoElectoral.objects.all().order_by('-fecha', '-hora_inicio')
    
    # Actualizar estados automáticamente
    for proceso in procesos:
        proceso.actualizar_estado()
    
    periodos = Periodo.objects.filter(estado='activo')
    
    return render(request, 'votacion/proceso/lista.html', {
        'procesos': procesos,
        'periodos': periodos,
        'titulo': 'Lista de Procesos Electorales'
    })

def editar_proceso(request, proceso_id):
    try:
        proceso = get_object_or_404(ProcesoElectoral, id=proceso_id)
        periodos = Periodo.objects.filter(estado='activo')
        
        if request.method == 'POST':
            nombre = request.POST.get('nombre')
            periodo_id = request.POST.get('periodo')
            fecha = request.POST.get('fecha')
            hora_inicio = request.POST.get('hora_inicio')
            hora_fin = request.POST.get('hora_fin')
            descripcion = request.POST.get('descripcion')

            periodo = get_object_or_404(Periodo, id=periodo_id)
            
            proceso.nombre = nombre
            proceso.periodo = periodo
            proceso.fecha = fecha
            proceso.hora_inicio = hora_inicio
            proceso.hora_fin = hora_fin
            proceso.descripcion = descripcion
            proceso.save()
            
            messages.success(request, 'Proceso electoral actualizado exitosamente')
            return redirect('votacion:lista_procesos')
        else:
            return render(request, 'votacion/proceso/editar.html', {
                'proceso': proceso,
                'periodos': periodos,
                'titulo': 'Editar Proceso Electoral'
            })
    except Exception as e:
        messages.error(request, f'Error al editar el proceso: {str(e)}')
        return redirect('votacion:lista_procesos')

def eliminar_proceso(request, proceso_id):
    try:
        proceso = get_object_or_404(ProcesoElectoral, id=proceso_id)
        
        if request.method == 'POST':
            proceso.delete()
            messages.success(request, 'Proceso electoral eliminado exitosamente')
            return redirect('votacion:lista_procesos')
        else:
            return render(request, 'votacion/proceso/eliminar.html', {
                'proceso': proceso,
                'titulo': 'Eliminar Proceso Electoral'
            })
    except Exception as e:
        messages.error(request, f'Error al eliminar el proceso: {str(e)}')
        return redirect('votacion:lista_procesos')

def obtener_proceso_activo(request):
    # Buscar el primer proceso activo
    try:
        procesos = ProcesoElectoral.objects.all()
        proceso_activo = None
        
        # Buscar el primer proceso que esté activo
        for proceso in procesos:
            if proceso.esta_activo():
                proceso_activo = proceso
                break
        
        if proceso_activo:
            return redirect('votacion:papeleta_votacion', proceso_id=proceso_activo.id)
        else:
            messages.warning(request, 'No hay procesos electorales activos en este momento')
            return redirect('votacion:lista_procesos')
    except Exception as e:
        messages.error(request, f'Error al buscar proceso activo: {str(e)}')
        return redirect('votacion:lista_procesos')

def papeleta_votacion(request, proceso_id):
    # Verificar si el usuario está autenticado
    if not request.user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Debe iniciar sesión para acceder a la papeleta de votación',
                'redirect': reverse('administracion:index')
            }, status=403)
        messages.error(request, 'Debe iniciar sesión para acceder a la papeleta de votación')
        return redirect('administracion:index')
    
    # Obtener el ID del padrón de la sesión
    padron_id = request.session.get('padron_id')
    if not padron_id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'No se encontró la información del padrón. Por favor, inicie sesión nuevamente.',
                'redirect': reverse('administracion:index')
            }, status=400)
        messages.error(request, 'No se encontró la información del padrón. Por favor, inicie sesión nuevamente.')
        return redirect('administracion:index')
    
    # Obtener el proceso electoral
    proceso = get_object_or_404(ProcesoElectoral, id=proceso_id)
    
    # Verificar si el proceso está activo
    if not proceso.esta_activo():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'El proceso electoral no está activo',
                'redirect': reverse('votacion:lista_procesos')
            }, status=400)
        messages.error(request, 'El proceso electoral no está activo')
        return redirect('votacion:lista_procesos')
    
    # Obtener la información del padrón
    from Aplicaciones.padron.models import PadronElectoral
    try:
        padron = PadronElectoral.objects.get(id=padron_id)
        
        # Verificar si ya existe un voto para este proceso y votante
        if Voto.objects.filter(proceso_electoral_id=proceso_id, votante=padron).exists():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Usted ya ha emitido su voto para este proceso electoral',
                    'voto_ya_emitido': True
                }, status=400)
            messages.error(request, 'Usted ya ha emitido su voto para este proceso electoral')
            return redirect('administracion:index')
            
        # Verificar si el usuario ya votó (compatibilidad con el campo voto en PadronElectoral)
        if hasattr(padron, 'voto') and padron.voto:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Usted ya ha emitido su voto para este proceso electoral',
                    'voto_ya_emitido': True
                }, status=400)
            messages.error(request, 'Usted ya ha emitido su voto para este proceso electoral')
            return redirect('administracion:index')
            
    except PadronElectoral.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'No se encontró su registro en el padrón electoral',
                'redirect': reverse('administracion:index')
            }, status=400)
        messages.error(request, 'No se encontró su registro en el padrón electoral')
        return redirect('administracion:index')
    
    # Obtener todas las listas del periodo
    listas = Lista.objects.filter(periodo=proceso.periodo)
    
    # Registrar acceso a la papeleta (opcional, para auditoría)
    print(f"\nAcceso a papeleta - Proceso: {proceso.nombre}, Estudiante: {padron.nombre} {padron.apellidos}, Cédula: {padron.cedula}")
    
    listas_con_candidatos = []
    
    for lista in listas:
        candidatos = Candidato.objects.filter(
            lista=lista
        ).select_related('cargo').order_by('cargo__nombre_cargo')
        
        print(f"\nCandidatos para lista {lista.nombre_lista}:")
        for candidato in candidatos:
            print(f"- {candidato.cargo.nombre_cargo}: {candidato.nombre_candidato}")
        
        listas_con_candidatos.append({
            'lista': lista,
            'candidatos': candidatos
        })

    context = {
        'proceso': proceso,
        'listas_con_candidatos': listas_con_candidatos,
        'title': f'Votación - {proceso.nombre}',
        'nombre_votante': f'{padron.nombre} {padron.apellidos}'
    }
    
    return render(request, 'votacion/papeleta.html', context)

def registrar_voto(request, proceso_id):
    if not request.user.is_authenticated:
        messages.error(request, 'Debe iniciar sesión para votar')
        return redirect('administracion:index')
    
    if request.method != 'POST':
        messages.error(request, 'Método no permitido')
        return redirect('administracion:index')
    
    padron_id = request.session.get('padron_id')
    if not padron_id:
        messages.error(request, 'No se encontró la información del padrón')
        return redirect('administracion:index')
    
    from Aplicaciones.padron.models import PadronElectoral
    try:
        padron = PadronElectoral.objects.get(id=padron_id)
        proceso = get_object_or_404(ProcesoElectoral, id=proceso_id)
        
        # Verificar si ya existe un voto para este proceso y votante
        if Voto.objects.filter(proceso_electoral=proceso, votante=padron).exists():
            messages.error(request, 'Usted ya ha emitido su voto para este proceso electoral')
            return redirect('administracion:index')
        
        # Verificar si el usuario ya votó (compatibilidad con el campo voto en PadronElectoral)
        if hasattr(padron, 'voto') and padron.voto:
            messages.error(request, 'Usted ya ha emitido su voto para este proceso electoral')
            return redirect('administracion:index')
        
        # Obtener la lista seleccionada
        lista_id = request.POST.get('lista')
        if not lista_id:
            messages.error(request, 'Debe seleccionar una lista para votar')
            return redirect('votacion:papeleta_votacion', proceso_id=proceso_id)
        
        try:
            lista = Lista.objects.get(id=lista_id)
        except Lista.DoesNotExist:
            messages.error(request, 'La lista seleccionada no es válida')
            return redirect('votacion:papeleta_votacion', proceso_id=proceso_id)
        
        # Obtener los candidatos seleccionados
        candidatos_seleccionados = {}
        for key, value in request.POST.items():
            if key.startswith('candidato_'):
                cargo_id = key.split('_')[1]
                candidatos_seleccionados[cargo_id] = value
        
        # Validar que se hayan seleccionado todos los cargos obligatorios
        cargos_obligatorios = lista.cargo_set.filter(obligatorio=True)
        for cargo in cargos_obligatorios:
            if str(cargo.id) not in candidatos_seleccionados:
                messages.error(request, f'Debe seleccionar un candidato para el cargo: {cargo.nombre_cargo}')
                return redirect('votacion:papeleta_votacion', proceso_id=proceso_id)
        
        # Crear el voto
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        hash_voto = generar_hash_voto(proceso_id, padron_id, timestamp)
        
        voto = Voto(
            proceso_electoral=proceso,
            votante=padron,
            lista_votada=lista,
            hash_voto=hash_voto,
            fecha_hora_voto=timezone.now(),
            ip_voto=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        voto.save()
        
        # Actualizar el campo voto en el padrón (para compatibilidad)
        if hasattr(padron, 'voto'):
            padron.voto = True
            padron.save()
        
        # Registrar los votos por cargo
        for cargo_id, candidato_id in candidatos_seleccionados.items():
            try:
                cargo = Cargo.objects.get(id=cargo_id)
                candidato = Candidato.objects.get(id=candidato_id)
                voto.candidatos.add(candidato)
            except (Cargo.DoesNotExist, Candidato.DoesNotExist):
                continue
        
        # Registrar el voto en el log
        print(f"\nVOTO REGISTRADO - Proceso: {proceso.nombre}")
        print(f"Estudiante: {padron.nombre} {padron.apellidos}, Cédula: {padron.cedula}")
        print(f"Lista seleccionada: {lista.nombre_lista}")
        print(f"Candidatos seleccionados: {candidatos_seleccionados}")
        print(f"Hash del voto: {hash_voto}")
        
        messages.success(request, '¡Su voto ha sido registrado exitosamente!')
        return redirect('votacion:gracias_por_votar')
        
    except PadronElectoral.DoesNotExist:
        messages.error(request, 'No se encontró su registro en el padrón electoral')
        return redirect('administracion:index')
    except Exception as e:
        messages.error(request, f'Error al registrar el voto: {str(e)}')
        return redirect('votacion:papeleta_votacion', proceso_id=proceso_id)

def resultados_votacion(request, proceso_id):
    try:
        proceso = get_object_or_404(ProcesoElectoral, id=proceso_id)
        
        # Verificar si el usuario es administrador o tiene permisos para ver resultados
        if not request.user.is_authenticated or not request.user.is_staff:
            messages.error(request, 'No tiene permisos para ver los resultados')
            return redirect('administracion:index')
        
        # Obtener todos los votos del proceso
        votos = Voto.objects.filter(proceso_electoral=proceso)
        total_votos = votos.count()
        
        # Obtener el conteo de votos por lista
        conteo_listas = votos.values('lista_votada__nombre_lista').annotate(
            total=Count('id')
        ).order_by('-total')
        
        # Calcular porcentajes
        for lista in conteo_listas:
            if total_votos > 0:
                lista['porcentaje'] = (lista['total'] / total_votos) * 100
            else:
                lista['porcentaje'] = 0
        
        # Obtener el conteo de votos por cargo
        cargos = Cargo.objects.filter(lista__in=conteo_listas.values('lista_votada')).distinct()
        resultados_cargos = {}
        
        for cargo in cargos:
            candidatos = Candidato.objects.filter(cargo=cargo)
            resultados_candidatos = []
            
            for candidato in candidatos:
                total_votos_candidato = Voto.objects.filter(
                    proceso_electoral=proceso,
                    candidatos=candidato
                ).count()
                
                resultados_candidatos.append({
                    'candidato': candidato,
                    'total_votos': total_votos_candidato,
                    'porcentaje': (total_votos_candidato / total_votos * 100) if total_votos > 0 else 0
                })
            
            # Ordenar por total de votos (de mayor a menor)
            resultados_candidatos.sort(key=lambda x: x['total_votos'], reverse=True)
            resultados_cargos[cargo] = resultados_candidatos
        
        context = {
            'proceso': proceso,
            'total_votos': total_votos,
            'conteo_listas': conteo_listas,
            'resultados_cargos': resultados_cargos,
            'title': f'Resultados - {proceso.nombre}'
        }
        
        return render(request, 'votacion/resultados.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al generar los resultados: {str(e)}')
        return redirect('votacion:lista_procesos')
