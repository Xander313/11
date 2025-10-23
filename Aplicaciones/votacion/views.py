from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.template.loader import get_template
from django.views import View
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO
import base64
import re
import os

from .models import ProcesoElectoral, Voto, CarnetVotacion
from Aplicaciones.periodo.models import Periodo
from Aplicaciones.elecciones.models import Lista, Candidato, Cargo
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

    # Obtener los períodos activos (insensible a mayúsculas/minúsculas)
    periodos = Periodo.objects.filter(estado__iexact='activo')
    print(f"Períodos encontrados: {list(periodos.values_list('nombre', flat=True))}")
    return render(request, 'votacion/proceso/iniciar.html', {'periodos': periodos})

def lista_procesos(request):
    procesos = ProcesoElectoral.objects.all().order_by('-fecha', '-hora_inicio')
    
    # Actualizar estados automáticamente
    for proceso in procesos:
        proceso.actualizar_estado()
    
    periodos = Periodo.objects.filter(estado__iexact='activo')
    
    return render(request, 'votacion/proceso/lista.html', {
        'procesos': procesos,
        'periodos': periodos,
        'titulo': 'Lista de Procesos Electorales'
    })

def editar_proceso(request, proceso_id):
    try:
        proceso = get_object_or_404(ProcesoElectoral, id=proceso_id)
        periodos = Periodo.objects.filter(estado__iexact='activo')
        
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
    # Verificar autenticación mediante sesión personalizada
    if not request.session.get('padron_autenticado'):
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
    if not request.session.get('padron_autenticado'):
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
        
        # Obtener el tipo de voto
        tipo_voto = request.POST.get('tipo_voto')
        
        # Inicializar variables
        lista = None
        candidatos_seleccionados = {}
        
        # Si no es voto en blanco ni nulo, obtener la lista y candidatos
        if tipo_voto not in ['blanco', 'nulo']:
            lista_id = request.POST.get('lista')
            if not lista_id:
                messages.error(request, 'Debe seleccionar una lista para votar')
                return redirect('votacion:papeleta_votacion', proceso_id=proceso_id)
            
            try:
                lista = Lista.objects.get(id=lista_id)
            except Lista.DoesNotExist:
                messages.error(request, 'La lista seleccionada no es válida')
                return redirect('votacion:papeleta_votacion', proceso_id=proceso_id)
            
            # Obtener los candidatos seleccionados solo si es un voto por lista
            for key, value in request.POST.items():
                if key.startswith('candidato_'):
                    cargo_id = key.split('_')[1]
                    candidatos_seleccionados[cargo_id] = value
        
        # Crear el voto
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        hash_voto = generar_hash_voto(proceso_id, padron_id, timestamp)
        
        # Determinar si es voto en blanco o nulo
        es_blanco = tipo_voto == 'blanco'
        es_nulo = tipo_voto == 'nulo'
        
        voto = Voto(
            proceso_electoral=proceso,
            votante=padron,
            lista=lista if not (es_blanco or es_nulo) else None,
            es_blanco=es_blanco,
            es_nulo=es_nulo,
            hash_voto=hash_voto
        )
        voto.save()
        
        # Actualizar el campo voto en el padrón (para compatibilidad)
        if hasattr(padron, 'voto'):
            padron.voto = True
            padron.save()
        
        # Registrar los votos por candidato
        for candidato_id in candidatos_seleccionados.values():
            try:
                candidato = Candidato.objects.get(id=candidato_id, lista=lista)
                voto.candidatos.add(candidato)
            except Candidato.DoesNotExist:
                continue
        
        # Registrar el voto en el log
        print(f"\nVOTO REGISTRADO - Proceso: {proceso.nombre}")
        print(f"Estudiante: {padron.nombre} {padron.apellidos}, Cédula: {padron.cedula}")
        if lista:
            print(f"Lista seleccionada: {lista.nombre_lista}")
        else:
            print("Voto en blanco o nulo")
        print(f"Hash del voto: {hash_voto}")
        
        # Generar el carnet de votación
        from .utils import generar_carnet_votacion
        carnet = generar_carnet_votacion(voto)
        
        # Enviar el correo con el comprobante
        from .utils import enviar_comprobante_email
        enviar_comprobante_email(carnet)
        
        messages.success(request, '¡Su voto ha sido registrado exitosamente! Se ha enviado un correo con su comprobante de votación.')
        return redirect('administracion:index')
        
    except PadronElectoral.DoesNotExist:
        messages.error(request, 'No se encontró su registro en el padrón electoral')
        return redirect('administracion:index')
    except Exception as e:
        messages.error(request, f'Error al registrar el voto: {str(e)}')
        return redirect('administracion:index')


def mostrar_carnet(request):
    """
    Muestra el carnet de votación después de un voto exitoso
    """
    if not request.session.get('padron_autenticado'):
        messages.error(request, 'Debe iniciar sesión para ver el carnet de votación')
        return redirect('administracion:index')
    
    carnet_id = request.session.get('carnet_id')
    if not carnet_id:
        messages.error(request, 'No se encontró información del carnet de votación')
        return redirect('administracion:index')
    
    from .models import CarnetVotacion
    try:
        carnet = CarnetVotacion.objects.get(id=carnet_id)
        
        # Eliminar el ID del carnet de la sesión para que no se muestre de nuevo
        if 'carnet_id' in request.session:
            del request.session['carnet_id']
            
        return render(request, 'votacion/carnet_votacion.html', {
            'carnet': carnet,
            'fecha_emision': carnet.fecha_emision.strftime('%d/%m/%Y %H:%M:%S'),
            'fecha_votacion': carnet.fecha_votacion.strftime('%d/%m/%Y %H:%M:%S')
        })
        
    except CarnetVotacion.DoesNotExist:
        messages.error(request, 'El carnet de votación solicitado no existe')
        return redirect('administracion:index')
    except Exception as e:
        messages.error(request, f'Error al mostrar el carnet de votación: {str(e)}')
        return redirect('administracion:index')
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

class GenerarCarnetPDF(View):
    """
    Vista para generar un PDF del carnet de votación con código QR de verificación
    """
    def get(self, request, carnet_id):
        # Obtener el carnet
        carnet = get_object_or_404(CarnetVotacion, id=carnet_id)
        
        # Crear un objeto HttpResponse con las cabeceras PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="carnet_votacion_{carnet.voto.votante.cedula}.pdf"'
        
        # Tamaño del documento (tamaño de carnet: 85.6mm x 54mm en puntos - 1mm = 2.83465pt)
        width, height = 242.65, 153  # 85.6mm x 54mm en puntos
        
        # Crear el objeto PDF con el tamaño del carnet
        p = canvas.Canvas(response, pagesize=(width, height))
        
        # Fondo del carnet
        p.setFillColorRGB(0.95, 0.95, 0.95)  # Gris claro
        p.rect(0, 0, width, height, fill=1, stroke=0)
        
        # Cabecera del carnet
        p.setFillColorRGB(0, 0.4, 0.8)  # Azul
        p.rect(0, height - 30, width, 30, fill=1, stroke=0)
        
        # Título del carnet
        p.setFillColorRGB(1, 1, 1)  # Blanco
        p.setFont("Helvetica-Bold", 12)
        p.drawCentredString(width/2, height - 23, "CARNET DE VOTACIÓN")
        
        # Sección de información
        p.setFillColorRGB(0, 0, 0)  # Negro
        
        # Logo (si está disponible)
        try:
            from Aplicaciones.configuracion.models import LogoConfig
            logo_config = LogoConfig.objects.first()
            if logo_config and logo_config.logo_1:
                from django.core.files.storage import default_storage
                from django.conf import settings
                
                logo_path = logo_config.logo_1.path
                if default_storage.exists(logo_path):
                    img = ImageReader(logo_path)
                    # Ajustar la imagen al tamaño deseado (60x60)
                    p.drawImage(img, 20, height - 100, width=60, height=60, mask='auto')
        except Exception as e:
            print(f"Error al cargar el logo: {str(e)}")
        
        # Información del votante
        p.setFont("Helvetica-Bold", 10)
        p.drawString(20, height - 70, "NOMBRE:")
        p.setFont("Helvetica", 10)
        p.drawString(70, height - 70, f"{carnet.voto.votante.nombre} {carnet.voto.votante.apellidos}")
        
        p.setFont("Helvetica-Bold", 10)
        p.drawString(20, height - 85, "CÉDULA:")
        p.setFont("Helvetica", 10)
        p.drawString(70, height - 85, carnet.voto.votante.cedula)
        
        p.setFont("Helvetica-Bold", 10)
        p.drawString(20, height - 100, "PROCESO:")
        p.setFont("Helvetica", 10)
        # Ajustar el texto del proceso para que quepa
        proceso = carnet.proceso_electoral
        if len(proceso) > 30:  # Si es muy largo, lo cortamos
            proceso = proceso[:27] + "..."
        p.drawString(70, height - 100, proceso)
        
        # Fecha de votación
        p.setFont("Helvetica-Bold", 8)
        p.drawString(20, height - 120, "FECHA DE VOTACIÓN:")
        p.setFont("Helvetica", 8)
        p.drawString(20, height - 130, carnet.fecha_votacion.strftime('%d/%m/%Y %H:%M'))
        
        # Código QR con la URL de verificación
        try:
            # Construir la URL de verificación usando la configuración de SITE_URL
            from django.urls import reverse
            from django.conf import settings
            
            # Usar SITE_URL de la configuración
            dominio = settings.SITE_URL
            # Asegurarse de que el dominio no termine con /
            dominio = dominio.rstrip('/')
            
            # Construir la URL completa
            url_verificacion = f"{dominio}{reverse('votacion:verificar_carnet', kwargs={'codigo_verificacion': carnet.codigo_verificacion})}"
            
            # Generar el código QR con la URL de verificación
            import qrcode
            from io import BytesIO
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=3, border=2)
            qr.add_data(url_verificacion)
            qr.make(fit=True)
            
            # Crear la imagen del código QR
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Guardar la imagen en un buffer
            buffer = BytesIO()
            qr_img.save(buffer, format='PNG')
            buffer.seek(0)
            
            # Dibujar el código QR en el PDF
            qr_reader = ImageReader(buffer)
            qr_size = 80  # Tamaño del código QR
            qr_x = width - qr_size - 20  # 20px del borde derecho
            qr_y = height - qr_size - 20  # 20px del borde inferior
            p.drawImage(qr_reader, qr_x, qr_y, width=qr_size, height=qr_size)
            
            # Texto debajo del QR
            p.setFont("Helvetica", 6)
            p.drawCentredString(qr_x + qr_size/2, qr_y - 10, "Escanear para verificar")
            
        except Exception as e:
            print(f"Error al generar el código QR: {str(e)}")
        
        # Código de verificación
        p.setFont("Helvetica-Bold", 8)
        p.drawString(20, 30, "CÓDIGO DE VERIFICACIÓN:")
        p.setFont("Helvetica", 8)
        p.drawString(20, 20, carnet.codigo_verificacion)
        
        # Pie de página
        p.setFont("Helvetica", 6)
        p.drawCentredString(width/2, 10, "Sistema de Votación Electrónica - Escuela Riobamba")
        
        # Cerrar el objeto PDF
        p.showPage()
        p.save()
        
        return response
        
        return response

def verificar_carnet(request, codigo_verificacion):
    """
    Vista para verificar un carnet de votación mediante su código de verificación
    Esta vista ahora ofrece la opción de ver los detalles o descargar un PDF completo
    """
    try:
        # Buscar el carnet por su código de verificación
        carnet = get_object_or_404(CarnetVotacion, codigo_verificacion=codigo_verificacion)
        
        # Verificar si se solicitó la descarga del PDF (por defecto siempre descargar PDF)
        formato = request.GET.get('formato', 'pdf')
        
        if formato == 'pdf' or True:  # Siempre descargar PDF
            # Redireccionar a la vista que genera el PDF del votante completo
            return redirect('votacion:descargar_datos_votante', carnet_id=carnet.id)
        else:
            # Renderizar la plantilla de verificación con un botón para descargar PDF
            # Este código no se ejecutará debido a la condición (formato == 'pdf' or True)
            # pero lo mantenemos por si en el futuro queremos tener ambas opciones
            return render(request, 'votacion/verificar_carnet.html', {
                'carnet': carnet,
                'verificado': True
            })
        
    except Exception as e:
        messages.error(request, f'Error al verificar el carnet: {str(e)}')
        return render(request, 'votacion/verificar_carnet.html', {
            'verificado': False,
            'error': str(e)
        })


def descargar_datos_votante(request, carnet_id):
    """
    Vista para generar un PDF completo con todos los datos del votante
    """
    try:
        # Obtener el carnet y la configuración del logo institucional
        from Aplicaciones.configuracion.models import LogoConfig
        carnet = get_object_or_404(CarnetVotacion, id=carnet_id)
        logo_config = LogoConfig.objects.first()
        
        # Crear un objeto HttpResponse con las cabeceras PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="datos_votante_{carnet.voto.votante.cedula}.pdf"'
        
        # Usar tamaño carta para este PDF
        width, height = letter
        
        # Crear el objeto PDF
        p = canvas.Canvas(response, pagesize=letter)
        
        # Añadir el logo institucional a la izquierda del título
        if logo_config and logo_config.logo_1:
            try:
                # Obtener la ruta del archivo
                logo_path = logo_config.logo_1.path
                
                # Verificar si el archivo existe
                if os.path.exists(logo_path):
                    # Tamaño y posición del sello - al lado del título
                    logo_width = 80
                    logo_height = 80
                    logo_x = 70  # Posición a la izquierda
                    logo_y = height - 90  # Alineado con los títulos
                    
                    # Dibujar el logo sin bordes negros
                    p.drawImage(logo_path, logo_x, logo_y, width=logo_width, height=logo_height, preserveAspectRatio=True, mask='auto')
            except Exception as e:
                print(f"Error al cargar el sello junto al título: {str(e)}")
        
        # Añadir un título (más a la derecha para dar espacio al logo)
        p.setFont("Helvetica-Bold", 18)
        p.drawString(180, height - 50, "CERTIFICADO DE VOTACIÓN")
        
        p.setFont("Helvetica-Bold", 14)
        p.drawString(180, height - 80, "ESCUELA DE EDUCACIÓN BÁSICA RIOBAMBA")
        
        # Línea horizontal
        p.setStrokeColor('#3b82f6')
        p.line(50, height - 100, width - 50, height - 100)
        
        # Datos del votante
        y_pos = height - 140
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y_pos, "DATOS DEL VOTANTE:")
        y_pos -= 25
        
        # Información del votante
        votante = carnet.voto.votante
        proceso = carnet.voto.proceso_electoral
        
        # Añadir datos personales
        p.setFont("Helvetica-Bold", 11)
        p.drawString(60, y_pos, "Nombre completo:")
        p.setFont("Helvetica", 11)
        p.drawString(200, y_pos, f"{votante.nombre} {votante.apellidos}")
        y_pos -= 20
        
        p.setFont("Helvetica-Bold", 11)
        p.drawString(60, y_pos, "Cédula de identidad:")
        p.setFont("Helvetica", 11)
        p.drawString(200, y_pos, votante.cedula)
        y_pos -= 20
        
        p.setFont("Helvetica-Bold", 11)
        p.drawString(60, y_pos, "Correo electrónico:")
        p.setFont("Helvetica", 11)
        p.drawString(200, y_pos, votante.correo if votante.correo else "No registrado")
        y_pos -= 40
        
        # Datos de la votación
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y_pos, "DATOS DEL PROCESO ELECTORAL:")
        y_pos -= 25
        
        p.setFont("Helvetica-Bold", 11)
        p.drawString(60, y_pos, "Proceso electoral:")
        p.setFont("Helvetica", 11)
        p.drawString(200, y_pos, proceso.nombre)
        y_pos -= 20
        
        p.setFont("Helvetica-Bold", 11)
        p.drawString(60, y_pos, "Período:")
        p.setFont("Helvetica", 11)
        p.drawString(200, y_pos, proceso.periodo.nombre)
        y_pos -= 20
        
        p.setFont("Helvetica-Bold", 11)
        p.drawString(60, y_pos, "Fecha de votación:")
        p.setFont("Helvetica", 11)
        p.drawString(200, y_pos, carnet.fecha_votacion.strftime('%d/%m/%Y'))
        y_pos -= 20
        
        
       
        
        # Generar código QR para verificación
        try:
            import qrcode
            from io import BytesIO
            
            # URL de verificación del carnet
            url_verificacion = request.build_absolute_uri(
                reverse('votacion:verificar_carnet', kwargs={'codigo_verificacion': carnet.codigo_verificacion})
            )
            
            # Generar el código QR
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url_verificacion)
            qr.make(fit=True)
            
            # Crear la imagen del QR
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Guardar la imagen del QR en un buffer
            buffer = BytesIO()
            qr_img.save(buffer, format='PNG')
            buffer.seek(0)
            
            # Dibujar el código QR en el PDF centrado
            qr_reader = ImageReader(buffer)
            qr_size = 100  # Tamaño del código QR
            # Centrar el QR horizontalmente
            qr_x = (width - qr_size) / 2
            p.drawImage(qr_reader, qr_x, y_pos - qr_size, width=qr_size, height=qr_size)
            
            # Texto debajo del QR, también centrado
            p.setFont("Helvetica", 8)
            p.drawCentredString(width/2, y_pos - qr_size - 15, "Escanear para verificar")
            
        except Exception as e:
            print(f"Error al generar el código QR: {str(e)}")
        
        # Se mantiene solo el logo del encabezado (el que aparece junto al título)
        
        # Sello de autenticidad
        y_pos = 150  # Posición del sello
        p.setFont("Helvetica-Bold", 12)
        p.drawCentredString(width/2, y_pos, "DOCUMENTO VÁLIDO COMO CERTIFICADO DE VOTACIÓN")
        y_pos -= 20
        
        # Pie de página
        p.setFont("Helvetica", 8)
        p.drawCentredString(width/2, 50, f"Certificado generado el {timezone.now().strftime('%d/%m/%Y')}")  
        p.drawCentredString(width/2, 35, "Este documento certifica la participación del votante en el proceso electoral")
        p.drawCentredString(width/2, 20, "Sistema de Votación Electrónica - Escuela de Educación Básica Riobamba")
        
        # Cerrar el objeto PDF
        p.showPage()
        p.save()
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error al generar el PDF con los datos del votante: {str(e)}')
        return redirect('administracion:index')

def registrar_voto(request, proceso_id):
    if not request.session.get('padron_autenticado'):
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
        
        # Obtener el tipo de voto
        tipo_voto = request.POST.get('tipo_voto')
        
        # Inicializar variables
        lista = None
        candidatos_seleccionados = {}
        
        # Si no es voto en blanco ni nulo, obtener la lista y candidatos
        if tipo_voto not in ['blanco', 'nulo']:
            lista_id = request.POST.get('lista')
            if not lista_id:
                messages.error(request, 'Debe seleccionar una lista para votar')
                return redirect('votacion:papeleta_votacion', proceso_id=proceso_id)
            
            try:
                lista = Lista.objects.get(id=lista_id)
            except Lista.DoesNotExist:
                messages.error(request, 'La lista seleccionada no es válida')
                return redirect('votacion:papeleta_votacion', proceso_id=proceso_id)
            
            # Obtener los candidatos seleccionados solo si es un voto por lista
            for key, value in request.POST.items():
                if key.startswith('candidato_'):
                    cargo_id = key.split('_')[1]
                    candidatos_seleccionados[cargo_id] = value
        
        # Crear el voto
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        hash_voto = generar_hash_voto(proceso_id, padron_id, timestamp)
        
        # Determinar si es voto en blanco o nulo
        es_blanco = tipo_voto == 'blanco'
        es_nulo = tipo_voto == 'nulo'
        
        voto = Voto(
            proceso_electoral=proceso,
            votante=padron,
            lista=lista if not (es_blanco or es_nulo) else None,
            es_blanco=es_blanco,
            es_nulo=es_nulo,
            hash_voto=hash_voto
        )
        voto.save()
        
        # Actualizar el campo voto en el padrón (para compatibilidad)
        if hasattr(padron, 'voto'):
            padron.voto = True
            padron.save()
        
        # Registrar los votos por candidato
        for candidato_id in candidatos_seleccionados.values():
            try:
                candidato = Candidato.objects.get(id=candidato_id, lista=lista)
                voto.candidatos.add(candidato)
            except Candidato.DoesNotExist:
                continue
        
        # Registrar el voto en el log
        print(f"\nVOTO REGISTRADO - Proceso: {proceso.nombre}")
        print(f"Estudiante: {padron.nombre} {padron.apellidos}, Cédula: {padron.cedula}")
        if lista:
            print(f"Lista seleccionada: {lista.nombre_lista}")
        else:
            print("Voto en blanco o nulo")
        print(f"Hash del voto: {hash_voto}")
        
        # Generar el carnet de votación
        from .utils import generar_carnet_votacion
        carnet = generar_carnet_votacion(voto)
        
        # Enviar el correo con el comprobante
        from .utils import enviar_comprobante_email
        enviar_comprobante_email(carnet)
        
        messages.success(request, '¡Su voto ha sido registrado exitosamente! Se ha enviado un correo con su comprobante de votación.')
        return redirect('administracion:index')
        
    except PadronElectoral.DoesNotExist:
        messages.error(request, 'No se encontró su registro en el padrón electoral')
        return redirect('administracion:index')
    except Exception as e:
        messages.error(request, f'Error al registrar el voto: {str(e)}')
        return redirect('administracion:index')
