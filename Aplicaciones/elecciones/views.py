from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.db.models import Q, Count
from django.utils import timezone
from django.urls import reverse
import json
from .models import Candidato, Lista, Cargo
from Aplicaciones.periodo.models import Periodo
from Aplicaciones.padron.models import PadronElectoral
from django.db.models import Q

def buscar_cedula_por_nombre(request):
    nombre = request.GET.get('nombre', '').strip()
    
    if not nombre:
        return JsonResponse({'error': 'Nombre no proporcionado'}, status=400)
    
    try:
        # Imprimir todos los registros para depuración
        print(f"Buscando registros con nombre: {nombre}")
        
        # Buscar en PadronElectoral usando búsqueda parcial insensitive a mayúsculas
        padrones = PadronElectoral.objects.filter(
            Q(nombre__icontains=nombre) | 
            Q(apellidos__icontains=nombre)
        )
        
        # Imprimir número de registros encontrados
        print(f"Registros encontrados: {padrones.count()}")
        
        # Si hay registros, tomar el primero
        padron = padrones.first()
        
        if padron:
            # Imprimir detalles del registro encontrado
            print(f"Registro encontrado - Cédula: {padron.cedula}, Nombre: {padron.nombre} {padron.apellidos}")
            return JsonResponse({
                'cedula': padron.cedula,
                'nombre': f'{padron.nombre} {padron.apellidos}'
            })
        else:
            # Imprimir mensaje si no se encuentra ningún registro
            print(f"No se encontraron registros para: {nombre}")
            return JsonResponse({'error': 'No se encontró ninguna persona'}, status=404)
    
    except Exception as e:
        # Imprimir cualquier error que ocurra
        print(f"Error en buscar_cedula_por_nombre: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


def listar_listas(request):
    try:
        # Primero verificamos si hay algún período activo
        periodo_actual = Periodo.objects.get(
            fecha_inicio__lte=timezone.now(),
            fecha_fin__gte=timezone.now()
        )
        
        listas = Lista.objects.filter(periodo=periodo_actual)
        periodos = Periodo.objects.all()
        
        # Obtener todos los candidatos de cada lista con sus cargos
        listas_con_candidatos = []
        for lista in listas:
            # Buscar el presidente
            presidente = Candidato.objects.filter(
                lista=lista,
                cargo__nombre_cargo__icontains='presidente'
            ).first()
            
            # Obtener todos los candidatos de la lista ordenados por cargo
            candidatos = Candidato.objects.filter(
                lista=lista
            ).select_related('cargo').order_by('cargo__nombre_cargo')
            
            # Agregar la lista, presidente y candidatos
            listas_con_candidatos.append({
                'lista': lista,
                'presidente': presidente,
                'candidatos': candidatos
            })
        
        # Convertir mensajes a JSON
        messages_list = [{'message': m.message, 'tags': m.tags} for m in messages.get_messages(request)]
        
        return render(request, 'lista/agregarlista.html', {
            'listas': listas_con_candidatos,
            'periodo_actual': periodo_actual,
            'periodos': periodos,
            'messages_json': json.dumps(messages_list)
        })
        
    except Periodo.DoesNotExist:
        # Si no hay período activo, mostramos un mensaje de error
        messages.error(request, 'No hay un período académico activo. Por favor, contacte al administrador.')
        return render(request, 'lista/agregarlista.html', {
            'listas': [],
            'periodo_actual': None,
            'periodos': Periodo.objects.all(),
            'messages_json': json.dumps([{'message': 'No hay un período académico activo. Por favor, contacte al administrador.', 'tags': 'error'}])
        })

def agregar_lista(request):
    periodos = Periodo.objects.all()
    print("\nIntentando agregar nueva lista...")
    print(f"Método de solicitud: {request.method}")
    print(f"POST data: {request.POST}")
    print(f"FILES data: {request.FILES}")
    
    if request.method == 'POST':
        print("Método POST recibido")
        nombre_lista = request.POST.get('nombre_lista', '').strip()
        frase = request.POST.get('frase', '').strip()
        periodo_id = request.POST.get('periodo')
        imagen = request.FILES.get('imagen')
        color = request.POST.get('color', '').strip()
        
        print(f"Datos recibidos:")
        print(f"- Nombre lista: {nombre_lista}")
        print(f"- Frase: {frase}")
        print(f"- Periodo ID: {periodo_id}")
        print(f"- Imagen: {imagen}")
        print(f"- Color: {color}")
        
        # Validar que no haya campos vacíos
        if not nombre_lista:
            print("Error: Nombre de lista vacío")
            messages.error(request, 'El nombre de la lista no puede estar vacío')
            return render(request, 'lista/agregarlista.html', {
                'periodos': periodos,
                'errors': {'nombre_lista': 'El nombre de la lista es obligatorio'}
            })
        
        if not periodo_id:
            print("Error: Periodo no seleccionado")
            messages.error(request, 'Debe seleccionar un periodo')
            return render(request, 'lista/agregarlista.html', {
                'periodos': periodos,
                'errors': {'periodo': 'Seleccione un periodo válido'}
            })
        
        try:
            periodo = Periodo.objects.get(id=periodo_id)
            print(f"Periodo encontrado: {periodo}")
            
            # Verificar si ya existe una lista con el mismo nombre en el periodo
            lista_existente = Lista.objects.filter(
                nombre_lista__iexact=nombre_lista, 
                periodo=periodo
            ).exists()
            
            if lista_existente:
                print(f"Error: Lista {nombre_lista} ya existe en el periodo {periodo}")
                messages.error(request, f'Ya existe una lista con el nombre {nombre_lista} en este periodo')
                return render(request, 'lista/agregarlista.html', {
                    'periodos': periodos,
                    'errors': {'nombre_lista': 'Lista duplicada'}
                })
            
            lista_data = {
                'nombre_lista': nombre_lista,
                'frase': frase,
                'periodo': periodo,
                'imagen': imagen
            }
            
            # Agregar color solo si se proporciona
            if color:
                lista_data['color'] = color
            
            print("Intentando crear lista con datos:", lista_data)
            try:
                lista = Lista.objects.create(**lista_data)
                print(f"Lista creada exitosamente con ID: {lista.id}")
                
                messages.success(request, f'Lista {lista.nombre_lista} creada exitosamente')
                return redirect('listar_listas')
            except Exception as e:
                print(f"Error al crear lista: {str(e)}")
                messages.error(request, f'Error al crear lista: {str(e)}')
                return render(request, 'lista/agregarlista.html', {
                    'periodos': periodos,
                    'errors': {'general': str(e)}
                })
            
        except Periodo.DoesNotExist:
            print(f"Error: No se encontró el periodo con ID {periodo_id}")
            messages.error(request, 'Periodo seleccionado no es válido')
            return render(request, 'lista/agregarlista.html', {
                'periodos': periodos,
                'errors': {'periodo': 'Periodo no válido'}
            })
        except Exception as e:
            print(f"Error al crear la lista: {str(e)}")
            messages.error(request, f'Error al crear la lista: {str(e)}')
            return render(request, 'lista/agregarlista.html', {
                'periodos': periodos,
                'errors': {'general': str(e)}
            })
    
    # GET request
    messages.success(request, 'Lista creada exitosamente')
    return render(request, 'lista/agregarlista.html', {
        'periodos': periodos
    })

def editar_lista(request, lista_id):
    lista = get_object_or_404(Lista, id=lista_id)
    
    if request.method == 'POST':
        # Obtener datos del formulario
        nombre_lista = request.POST.get('nombre_lista', '').strip()
        frase = request.POST.get('frase', '').strip()
        periodo_id = request.POST.get('periodo')
        color = request.POST.get('color', 'azul').strip()
        
        # Validaciones
        if not nombre_lista:
            messages.error(request, 'El nombre de la lista no puede estar vacío')
            messages_list = [{'message': m.message, 'tags': m.tags} for m in messages.get_messages(request)]
            return redirect('listar_listas')
        
        try:
            # Actualizar campos
            lista.nombre_lista = nombre_lista
            lista.frase = frase
            
            # Asegurarse de que el color no sea vacío
            if color and color.strip():
                lista.color = color.strip()
            else:
                # Si no se proporciona color, mantener el color existente
                # Si no hay color existente, usar 'azul' como predeterminado
                lista.color = lista.color or 'azul'
            
            # Actualizar periodo si es diferente
            if periodo_id:
                periodo = Periodo.objects.get(id=periodo_id)
                lista.periodo = periodo
            
            # Manejar imagen
            imagen = request.FILES.get('imagen')
            if imagen:
                lista.imagen = imagen
            
            # Guardar cambios
            lista.save()
            
            messages.success(request, f'Lista {lista.nombre_lista} actualizada exitosamente')
            messages_list = [{'message': m.message, 'tags': m.tags} for m in messages.get_messages(request)]
            return redirect('listar_listas')
        
        except Periodo.DoesNotExist:
            messages.error(request, 'Periodo seleccionado no es válido')
        except Exception as e:
            messages.error(request, f'Error al actualizar la lista: {str(e)}')
    
    messages_list = [{'message': m.message, 'tags': m.tags} for m in messages.get_messages(request)]
    messages.success(request, 'Lista actualizada exitosamente')
    return redirect('listar_listas')

def eliminar_lista(request, lista_id):
    if request.method != 'POST':
        return redirect('listar_listas')
        
    try:
        # Obtener la lista
        lista = get_object_or_404(Lista, id=lista_id)
        
        # Obtener candidatos asociados
        candidatos_asociados = lista.candidato_set.all()
        candidatos_count = candidatos_asociados.count()
        
        # Eliminar candidatos
        if candidatos_count > 0:
            for candidato in candidatos_asociados:
                candidato.delete()
        
        # Eliminar la lista
        nombre_lista = lista.nombre_lista
        lista.delete()
        
        messages.success(request, f'Lista {nombre_lista} y {candidatos_count} candidatos eliminados exitosamente')
        
    except Exception as e:
        messages.error(request, f'No se pudo eliminar la lista. Error: {str(e)}')
        
    return redirect('listar_listas')

#APARTADO DE CARGOS
def listar_cargos(request):
    try:
        # Verificar si hay un período activo
        periodo_actual = Periodo.objects.get(
            fecha_inicio__lte=timezone.now(),
            fecha_fin__gte=timezone.now()
        )
        periodos = Periodo.objects.all()
        cargos = Cargo.objects.filter(periodo=periodo_actual)
        
        # Convertir mensajes a JSON
        messages_list = [{'message': m.message, 'tags': m.tags} for m in messages.get_messages(request)]
        
        return render(request, 'cargos/agregarcargo.html', {
            'cargos': cargos,
            'periodo_actual': periodo_actual,
            'periodos': periodos,
            'messages_json': json.dumps(messages_list)
        })
        
    except Periodo.DoesNotExist:
        # Si no hay período activo, mostramos un mensaje de error
        messages.error(request, 'No hay un período académico activo. Por favor, contacte al administrador.')
        return render(request, 'cargos/agregarcargo.html', {
            'cargos': [],
            'periodo_actual': None,
            'periodos': Periodo.objects.all(),
            'messages_json': json.dumps([{'message': 'No hay un período académico activo. Por favor, contacte al administrador.', 'tags': 'error'}])
        })

def agregar_cargo(request, cargo_id=None):
    periodo_actual = Periodo.objects.get(
        fecha_inicio__lte=timezone.now(),
        fecha_fin__gte=timezone.now()
    )
    periodos = Periodo.objects.all()
    cargo = None
    
    # Si se proporciona cargo_id, es una edición
    if cargo_id:
        cargo = get_object_or_404(Cargo, id=cargo_id)
    
    if request.method == 'POST':
        # Obtener datos del formulario
        nombre_cargo = request.POST.get('nombre_cargo', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        periodo_id = request.POST.get('periodo')
        
        # Validaciones
        if not nombre_cargo:
            messages.error(request, 'El nombre del cargo no puede estar vacío')
            return render(request, 'cargos/agregarcargo.html', {
                'cargo': cargo,
                'periodo_actual': periodo_actual,
                'periodos': periodos
            })
        
        try:
            # Obtener periodo
            periodo = Periodo.objects.get(id=periodo_id)
            
            # Si es edición, actualizar cargo existente
            if cargo:
                cargo.nombre_cargo = nombre_cargo
                cargo.descripcion = descripcion or None
                cargo.periodo = periodo
                cargo.save()
                messages.success(request, 'Cargo actualizado correctamente')
            else:
                # Crear nuevo cargo
                cargo = Cargo.objects.create(
                    nombre_cargo=nombre_cargo,
                    descripcion=descripcion or None,
                    periodo=periodo
                )
                messages.success(request, 'Cargo creado correctamente')
            
            return redirect('listar_cargos')
        
        except Periodo.DoesNotExist:
            messages.error(request, 'Periodo seleccionado no es válido')
            return render(request, 'cargos/agregarcargo.html', {
                'cargo': cargo,
                'periodo_actual': periodo_actual,
                'periodos': periodos
            })
        except Exception as e:
            messages.error(request, f'Error al procesar el cargo: {str(e)}')
            return render(request, 'cargos/agregarcargo.html', {
                'cargo': cargo,
                'periodo_actual': periodo_actual,
                'periodos': periodos
            })
    
    # Si no es POST, renderizar la página normalmente
    cargos = Cargo.objects.filter(periodo=periodo_actual)
    messages_list = [{'message': m.message, 'tags': m.tags} for m in messages.get_messages(request)]
    
    return render(request, 'cargos/agregarcargo.html', {
        'cargos': cargos,
        'cargo': cargo,
        'periodo_actual': periodo_actual,
        'periodos': periodos,
        'messages_json': json.dumps(messages_list)
    })

def eliminar_cargo(request, cargo_id):
    if request.method == 'POST':
        try:
            # Obtener el cargo
            cargo = get_object_or_404(Cargo, id=cargo_id)
            
            # Obtener candidatos asociados
            candidatos_asociados = cargo.candidato_set.all()
            candidatos_count = candidatos_asociados.count()
            
            # Eliminar candidatos
            if candidatos_count > 0:
                for candidato in candidatos_asociados:
                    candidato.delete()
            
            # Eliminar el cargo
            nombre_cargo = cargo.nombre_cargo
            cargo.delete()
            
            # Agregar mensaje de éxito
            messages.success(request, 'Cargo eliminado correctamente')
            
            # Redirigir a la lista de cargos con el mensaje
            return redirect('listar_cargos')
        
        except Exception as e:
            import traceback
            print(f"Error al eliminar cargo: {str(e)}")
            traceback.print_exc()
            
            # Agregar mensaje de error
            messages.error(request, f'No se pudo eliminar el cargo: {str(e)}')
            
            # Redirigir a la lista de cargos con el mensaje de error
            return redirect('listar_cargos')
    else:
        # Mensaje de método no permitido
        messages.error(request, 'Método no permitido')
        return redirect('listar_cargos')




#APARTADO DE CANDIDATOS
def listar_candidatos(request):
    try:
        # Verificar si hay un período activo
        periodo_actual = Periodo.objects.get(
            fecha_inicio__lte=timezone.now(),
            fecha_fin__gte=timezone.now()
        )
        
        # Obtener candidatos del período actual
        candidatos = Candidato.objects.filter(periodo=periodo_actual).select_related('lista', 'cargo', 'periodo')
        
        # Convertir mensajes a JSON
        messages_list = [{'message': m.message, 'tags': m.tags} for m in messages.get_messages(request)]
        
        return render(request, 'candidatos/listar.html', {
            'candidatos': candidatos, 
            'periodo_actual': periodo_actual,
            'messages_json': json.dumps(messages_list)
        })
        
    except Periodo.DoesNotExist:
        # Si no hay período activo, mostramos un mensaje de error
        messages.error(request, 'No hay un período académico activo. Por favor, contacte al administrador.')
        return render(request, 'candidatos/listar.html', {
            'candidatos': [],
            'periodo_actual': None,
            'messages_json': json.dumps([{'message': 'No hay un período académico activo. Por favor, contacte al administrador.', 'tags': 'error'}])
        })

def agregar_candidato(request):
    if request.method == 'POST':
        try:
            print("Datos recibidos en POST:", request.POST)
            print("Archivos recibidos:", request.FILES)
            
            # Obtener datos comunes del formulario
            lista_id = request.POST.get('lista')
            periodo_id = request.POST.get('periodo')
            
            if not lista_id or not periodo_id:
                messages.error(request, 'Debe seleccionar una lista y un período')
                return redirect('agregar_candidato')
            
            # Obtener instancias relacionadas
            lista = Lista.objects.get(pk=lista_id)
            periodo = Periodo.objects.get(pk=periodo_id)
            
            # Procesar cada tipo de candidato
            tipos_candidato = ['principal', 'suplente', 'alterno']
            candidatos_creados = 0
            
            for tipo in tipos_candidato:
                # Obtener datos específicos del tipo de candidato
                nombre = request.POST.get(f'nombre_{tipo}')
                cargo_id = request.POST.get(f'cargo_{tipo}')
                cedula = request.POST.get(f'cedula_{tipo}')
                
                print(f"Procesando {tipo}:", {
                    'nombre': nombre,
                    'cargo_id': cargo_id,
                    'cedula': cedula
                })
                
                # Si no hay nombre o cargo, continuar con el siguiente tipo
                if not nombre or not cargo_id:
                    print(f"Saltando {tipo}: falta nombre o cargo")
                    continue
                
                try:
                    cargo = Cargo.objects.get(pk=cargo_id)
                    
                    # Verificar si el estudiante ya es candidato en otra lista en el mismo período
                    candidato_existente = Candidato.objects.filter(
                        Q(cedula_principal=cedula) | 
                        Q(cedula_suplente=cedula) | 
                        Q(cedula_alterno=cedula),
                        periodo=periodo
                    ).exclude(lista=lista).first()
                    
                    if candidato_existente:
                        messages.warning(
                            request, 
                            f'El estudiante {nombre} ya es candidato en la lista {candidato_existente.lista.nombre_lista} como {candidato_existente.get_tipo_candidato_display()}.'
                        )
                        continue
                    
                    # Crear el candidato
                    candidato = Candidato(
                        nombre_candidato=nombre,
                        lista=lista,
                        cargo=cargo,
                        periodo=periodo,
                        tipo_candidato=tipo.upper(),
                        **{f'cedula_{tipo}': cedula}  # Guardar la cédula en el campo correspondiente
                    )
                    
                    # Manejar la imagen si se subió
                    imagen_field = f'foto_{tipo}'
                    if imagen_field in request.FILES:
                        print(f"Imagen encontrada para {tipo}")
                        candidato.imagen = request.FILES[imagen_field]
                    
                    candidato.save()
                    print(f"Candidato {tipo} guardado correctamente")
                    candidatos_creados += 1
                    
                except Cargo.DoesNotExist:
                    print(f"Error: No se encontró el cargo para {tipo} con ID {cargo_id}")
                    messages.warning(request, f'No se encontró el cargo para el {tipo}')
                    continue
                except Exception as e:
                    print(f"Error al guardar {tipo}:", str(e))
                    messages.warning(request, f'Error al guardar el {tipo}: {str(e)}')
                    continue
            
            if candidatos_creados > 0:
                messages.success(request, f'Se agregaron {candidatos_creados} candidatos correctamente')
            else:
                messages.warning(request, 'No se agregó ningún candidato. Verifica los datos e inténtalo de nuevo.')
            
            return redirect('listar_candidatos')
            
        except (Lista.DoesNotExist, Periodo.DoesNotExist) as e:
            print("Error de lista o período no encontrado:", str(e))
            messages.error(request, 'Error: La lista o el período seleccionado no existe')
            return redirect('agregar_candidato')
        except Exception as e:
            print("Error general:", str(e))
            messages.error(request, f'Error al procesar el formulario: {str(e)}')
            return redirect('agregar_candidato')
    
    # GET request - Mostrar el formulario
    try:
        listas = Lista.objects.all()
        cargos = Cargo.objects.all()
        periodos = Periodo.objects.all()
        
        return render(request, 'candidatos/agregar.html', {
            'listas': listas,
            'cargos': cargos,
            'periodos': periodos,
            'tipos_candidato': Candidato.TIPOS_CANDIDATO
        })
    except Exception as e:
        print("Error al cargar el formulario:", str(e))
        messages.error(request, f'Error al cargar el formulario: {str(e)}')
        return redirect('listar_candidatos')

def editar_candidato(request, candidato_id):
    candidato = get_object_or_404(Candidato, pk=candidato_id)
    
    if request.method == 'POST':
        try:
            # Actualizar datos del formulario
            candidato.nombre_candidato = request.POST.get('nombre_candidato')
            candidato.lista_id = request.POST.get('lista')
            candidato.cargo_id = request.POST.get('cargo')
            candidato.periodo_id = request.POST.get('periodo')
            candidato.tipo_candidato = request.POST.get('tipo_candidato', 'PRINCIPAL')
            
            # Manejar la imagen si se subió una nueva
            if 'imagen' in request.FILES:
                candidato.imagen = request.FILES['imagen']
                
            candidato.save()
            messages.success(request, 'Candidato actualizado correctamente')
            return redirect('listar_candidatos')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar el candidato: {str(e)}')
    
    # Obtener datos para el formulario
    listas = Lista.objects.all()
    cargos = Cargo.objects.all()
    periodos = Periodo.objects.all()
    
    return render(request, 'candidatos/editar.html', {
        'candidato': candidato,
        'listas': listas,
        'cargos': cargos,
        'periodos': periodos,
        'tipos_candidato': Candidato.TIPOS_CANDIDATO
    })

def eliminar_candidato(request, candidato_id):
    candidato = get_object_or_404(Candidato, pk=candidato_id)
    if request.method == 'POST':
        try:
            candidato.delete()
            messages.success(request, 'Candidato eliminado correctamente')
        except Exception as e:
            messages.error(request, f'Error al eliminar el candidato: {str(e)}')
        return redirect('listar_candidatos')
    return render(request, 'candidatos/eliminar.html', {'candidato': candidato})

def buscar_nombre_por_cedula(request):
    busqueda = request.GET.get('cedula', '').strip()
    
    try:
        # Si la búsqueda es numérica, buscar por cédula que comience con esos números
        if busqueda.isdigit():
            padron = PadronElectoral.objects.filter(cedula__startswith=busqueda).first()
            if padron:
                return JsonResponse({
                    'nombre': f'{padron.nombre} {padron.apellidos}',
                    'cedula': padron.cedula,
                    'grado': padron.grado.nombre,
                    'paralelo': padron.paralelo.nombre
                })
        
        # Si no es numérica o no se encontró por cédula, buscar por nombre o apellido
        if len(busqueda) >= 3:
            padron = PadronElectoral.objects.filter(
                Q(nombre__icontains=busqueda) | 
                Q(apellidos__icontains=busqueda)
            ).first()
            
            if padron:
                return JsonResponse({
                    'nombre': f'{padron.nombre} {padron.apellidos}',
                    'cedula': padron.cedula,
                    'grado': padron.grado.nombre,
                    'paralelo': padron.paralelo.nombre
                })
        
        return JsonResponse({'nombre': None}, status=404)
        
    except Exception as e:
        print(f'Error en búsqueda: {str(e)}')
        return JsonResponse({'nombre': None}, status=400)

def buscar_nombre_por_cedula(request):
    if 'cedula' in request.GET:
        cedula = request.GET.get('cedula')
        try:
            # Buscar en el padrón electoral
            persona = PadronElectoral.objects.get(cedula=cedula)
            
            # Verificar si ya está en alguna lista
            periodo_actual = Periodo.objects.filter(
                fecha_inicio__lte=timezone.now(),
                fecha_fin__gte=timezone.now()
            ).first()
            
            en_otra_lista = None
            if periodo_actual:
                en_otra_lista = Candidato.objects.filter(
                    (Q(cedula_principal=cedula) | Q(cedula_suplente=cedula) | Q(cedula_alterno=cedula)) &
                    Q(periodo=periodo_actual)
                ).first()
            
            return JsonResponse({
                'success': True,
                'nombre': persona.nombre_completo,
                'cedula': persona.cedula,
                'grado': persona.grado.nombre if hasattr(persona, 'grado') and persona.grado else None,
                'paralelo': persona.paralelo.nombre if hasattr(persona, 'paralelo') and persona.paralelo else None,
                'en_otra_lista': {
                    'lista': en_otra_lista.lista.nombre_lista if en_otra_lista else None,
                    'tipo': en_otra_lista.get_tipo_candidato_display() if en_otra_lista else None
                } if en_otra_lista else None
            })
        except PadronElectoral.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'No se encontró ninguna persona con esta cédula'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'No se proporcionó cédula'}, status=400)

def limpiar_listas_huérfanas():
    """
    Función para eliminar listas que no tienen candidatos asociados
    Devuelve el número de listas eliminadas
    """
    # Encontrar listas que no tienen candidatos
    listas_huérfanas = Lista.objects.annotate(
        num_candidatos=Count('candidato')
    ).filter(num_candidatos=0)
    
    # Contar cuántas se van a eliminar
    total_eliminadas = listas_huérfanas.count()
    
    # Eliminar las listas huérfanas
    listas_huérfanas.delete()
    
    return total_eliminadas

def limpiar_listas_sin_candidatos(request):
    """
    Vista para limpiar listas sin candidatos
    """
    if request.method == 'POST':
        total_eliminadas = limpiar_listas_huérfanas()
        messages.success(request, f'Se eliminaron {total_eliminadas} listas sin candidatos')
        return HttpResponseRedirect(reverse('listar_listas'))
    
    # Si no es POST, redirigir a la lista de listas
    return HttpResponseRedirect(reverse('listar_listas'))

def verificar_estudiante_lista(request):
    """
    Vista para verificar si un estudiante ya está en otra lista
    """
    cedula = request.GET.get('cedula')
    if not cedula:
        return JsonResponse({'error': 'No se proporcionó cédula'}, status=400)
    
    try:
        periodo_actual = Periodo.objects.filter(
            fecha_inicio__lte=timezone.now(),
            fecha_fin__gte=timezone.now()
        ).first()
        
        if not periodo_actual:
            return JsonResponse({'en_otra_lista': False})
            
        candidato = Candidato.objects.filter(
            (Q(cedula_principal=cedula) | Q(cedula_suplente=cedula) | Q(cedula_alterno=cedula)) &
            Q(periodo=periodo_actual)
        ).first()
        
        if candidato:
            return JsonResponse({
                'en_otra_lista': True,
                'lista': candidato.lista.nombre_lista,
                'tipo': candidato.get_tipo_candidato_display()
            })
            
        return JsonResponse({'en_otra_lista': False})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
