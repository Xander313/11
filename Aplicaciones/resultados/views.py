from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, F
from Aplicaciones.votacion.models import ProcesoElectoral, Voto
from Aplicaciones.elecciones.models import Lista
from Aplicaciones.padron.models import PadronElectoral
import os
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound, FileResponse
from datetime import datetime
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.lib.colors import HexColor
from reportlab.platypus import PageBreak
from reportlab.platypus import Image, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER


@login_required
def resultados_votacion(request, proceso_id):
    proceso = get_object_or_404(ProcesoElectoral, id=proceso_id)
    
    # Verificar si el proceso ha finalizado (estado 'finalizado')
    if proceso.estado != 'finalizado':
        messages.warning(request, 'Los resultados solo están disponibles para procesos electorales finalizados.')
        return redirect('votacion:lista_procesos')  # Redirigir a la lista de procesos en la app de votación
    
    # Obtener votos por lista ordenados de mayor a menor
    votos_por_lista = Voto.objects.filter(
        proceso_electoral=proceso,
        lista__isnull=False
    ).values('lista').annotate(
        total=Count('id'),
        nombre_lista=F('lista__nombre_lista')
    ).order_by('-total')
    
    # Obtener total de votos
    total_votos = Voto.objects.filter(proceso_electoral=proceso).count()
    votos_blancos = Voto.objects.filter(proceso_electoral=proceso, es_blanco=True).count()
    votos_nulos = Voto.objects.filter(proceso_electoral=proceso, es_nulo=True).count()
    
    # Calcular porcentajes y determinar ganador
    resultados_por_lista = []
    ganador = None
    max_votos = 0
    
    for voto in votos_por_lista:
        lista = Lista.objects.get(id=voto['lista'])
        porcentaje = (voto['total'] / total_votos * 100) if total_votos > 0 else 0
        resultado = {
            'lista': lista,
            'votos': voto['total'],
            'porcentaje': porcentaje,
            'es_ganador': False
        }
        
        # Verificar si es el ganador actual
        if voto['total'] > max_votos:
            max_votos = voto['total']
            if ganador is not None:
                # Quitar condición de ganador del anterior
                for r in resultados_por_lista:
                    r['es_ganador'] = False
            resultado['es_ganador'] = True
            ganador = lista
        
        resultados_por_lista.append(resultado)
    
    # Calcular porcentajes de blancos y nulos
    porcentaje_blancos = (votos_blancos / total_votos * 100) if total_votos > 0 else 0
    porcentaje_nulos = (votos_nulos / total_votos * 100) if total_votos > 0 else 0
    
    # Obtener estadísticas de participación
    total_votantes = PadronElectoral.objects.filter(periodo=proceso.periodo).count()
    faltan_votar = total_votantes - total_votos
    porcentaje_participacion = (total_votos / total_votantes * 100) if total_votantes > 0 else 0
    
    context = {
        'proceso': proceso,
        'resultados_por_lista': resultados_por_lista,
        'ganador': ganador,
        'votos_ganador': max_votos,
        'votos_blancos': votos_blancos,
        'votos_nulos': votos_nulos,
        'porcentaje_blancos': porcentaje_blancos,
        'porcentaje_nulos': porcentaje_nulos,
        'total_votos': total_votos,
        'total_votantes': total_votantes,
        'faltan_votar': faltan_votar,
        'porcentaje_participacion': porcentaje_participacion
    }
    
    return render(request, 'resultados/resultados.html', context)

def lista_resultados(request):
    procesos = ProcesoElectoral.objects.all().order_by('-created_at')
    return render(request, 'resultados/lista_resultados.html', {
        'procesos': procesos,
        'titulo': 'Resultados de Procesos Electorales'
    })


#===============================================
# Funcion para descargar backup
#===============================================
@login_required
def descargar_backup_sqlite(request):
    try:
        ruta_db = settings.DATABASES['default']['NAME']
    except KeyError:
        return HttpResponseNotFound("Configuración de base de datos no encontrada")

    if os.path.exists(ruta_db):
        fecha_actual = datetime.now().strftime('%Y-%m-%d')
        nombre_archivo = f"backup_escuela_riobamba_{fecha_actual}.sqlite3"
        return FileResponse(open(ruta_db, 'rb'), as_attachment=True, filename=nombre_archivo)
    else:
        return HttpResponseNotFound(f"Archivo de base de datos no encontrado en: {ruta_db}")


@login_required

def generar_reporte_pdf(request, proceso_id):
    """Genera un PDF con los resultados del proceso electoral y el listado de votantes."""
    proceso = get_object_or_404(ProcesoElectoral, id=proceso_id)

    # -------------------------------
    # Resultados generales del proceso
    # -------------------------------
    votos_por_lista = Voto.objects.filter(
        proceso_electoral=proceso,
        lista__isnull=False
    ).values('lista').annotate(
        total=Count('id'),
        nombre_lista=F('lista__nombre_lista')
    ).order_by('-total')

    total_votos = Voto.objects.filter(proceso_electoral=proceso).count()
    votos_blancos = Voto.objects.filter(proceso_electoral=proceso, es_blanco=True).count()
    votos_nulos = Voto.objects.filter(proceso_electoral=proceso, es_nulo=True).count()

    resultados_por_lista = []
    max_votos = 0
    ganador = None
    for voto in votos_por_lista:
        lista = Lista.objects.get(id=voto['lista'])
        porcentaje = (voto['total'] / total_votos * 100) if total_votos > 0 else 0
        resultado = {
            'lista': lista,
            'votos': voto['total'],
            'porcentaje': porcentaje,
            'es_ganador': False
        }
        if voto['total'] > max_votos:
            max_votos = voto['total']
            for r in resultados_por_lista:
                r['es_ganador'] = False
            resultado['es_ganador'] = True
            ganador = lista
        resultados_por_lista.append(resultado)

    porcentaje_blancos = (votos_blancos / total_votos * 100) if total_votos > 0 else 0
    porcentaje_nulos = (votos_nulos / total_votos * 100) if total_votos > 0 else 0

    # -------------------------------
    # Generación del PDF
    # -------------------------------
    buffer = io.BytesIO()

    try:
        font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
        base_font = 'DejaVuSans'
    except Exception:
        base_font = 'Helvetica'

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )

    styles = getSampleStyleSheet()
    styles['Normal'].fontName = base_font
    styles['Heading1'].fontName = base_font
    styles['Heading2'].fontName = base_font

    elements = []

    # -------------------------------
    # Encabezado
    # -------------------------------
   # -------------------------------
    # Estilos
    # -------------------------------
    header_style = ParagraphStyle(
        'header_center', 
        alignment=TA_CENTER, 
        fontSize=14, 
        leading=16
    )
    title_style = ParagraphStyle(
        'title_center', 
        alignment=TA_CENTER, 
        fontSize=12, 
        leading=14
    )
    meta_style = ParagraphStyle(
        'meta_center', 
        alignment=TA_CENTER, 
        fontSize=10, 
        leading=12
    )

    # -------------------------------
    # Logo + Encabezado
    # -------------------------------
    from reportlab.platypus import Image, Paragraph, Table, TableStyle

    logo_path = '/home/xander/11/sistema_voto_ue_riobamba/static/images/logo1.png'
    logo = Image(logo_path, width=50, height=50)  # ajusta tamaño

    header_text = [
        [logo,
        Paragraph(
            "Unidad Educativa del Milenio '11 de Noviembre'<br/>"
            "Votaciones 22 y 23 de noviembre del 2025<br/>"
            f"Resultados Electorales - {proceso.nombre}",
            header_style
        )
        ]
    ]

    header_table = Table(header_text, colWidths=[60, doc.width-60])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (0,0), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))

    elements.append(header_table)
    elements.append(Spacer(1, 12))
    # -------------------------------
    # Tabla de resultados por lista
    # -------------------------------
    data = [["Lista", "Votos", "Porcentaje"]]
    for r in resultados_por_lista:
        nombre = getattr(r['lista'], 'nombre_lista', str(r['lista']))
        data.append([nombre, str(r['votos']), f"{r['porcentaje']:.2f}%"])

    data.append(["Votos en Blanco", str(votos_blancos), f"{porcentaje_blancos:.2f}%"])
    data.append(["Votos Nulos", str(votos_nulos), f"{porcentaje_nulos:.2f}%"])
    data.append(["TOTAL", str(total_votos), "100.00%"])

    table = Table(data, colWidths=[100*mm, 30*mm, 30*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1,-1), base_font),
        ('ALIGN', (1,1), (2,-1), 'CENTER'),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))


    elements.append(Spacer(1, 12))  # 12 puntos de espacio vertical (~1 línea)


    # -------------------------------
    # Gráfica de pastel de resultados
    # -------------------------------
    try:
        pie_labels = []
        pie_data = []
        for r in resultados_por_lista:
            nombre = getattr(r['lista'], 'nombre_lista', str(r['lista']))
            pie_labels.append(f"{nombre} ({r['porcentaje']:.1f}%)")
            pie_data.append(max(r['porcentaje'], 0))

        # Añadir blancos y nulos
        pie_labels.append(f"Blancos ({porcentaje_blancos:.1f}%)")
        pie_data.append(max(porcentaje_blancos, 0))
        pie_labels.append(f"Nulos ({porcentaje_nulos:.1f}%)")
        pie_data.append(max(porcentaje_nulos, 0))

        if sum(pie_data) > 0:
            drawing = Drawing(250, 200)

            pie = Pie()
            pie.x = 40
            pie.y = 10
            pie.width = 180  # más ancho
            pie.height = 180  # más alto

            pie.data = pie_data
            pie.labels = pie_labels
            drawing.add(pie)
            elements.append(drawing)
            elements.append(Spacer(1, 12))
    except Exception:
        pass

    # -------------------------------
    # Resumen de votación
    # -------------------------------





    elements.append(Paragraph("Resumen de Votación", styles['Heading2']))
    elements.append(Spacer(1, 6))
    total_padron = PadronElectoral.objects.filter(periodo=proceso.periodo).count()
    stats_data = [
        ["Votantes Habilitados", str(total_padron)],
        ["Votos Emitidos", str(total_votos)],
        ["No Votaron", str(total_padron - total_votos)],
    ]
    stats_table = Table(stats_data, colWidths=[80*mm, 40*mm])
    stats_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), base_font),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT')
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 12))
    
        # -------------------------------
    # Firma del documento
    # -------------------------------
    elements.append(Spacer(1, 24))
    sig_table = Table([
        ['_______________________________'],
        ['Firma Rectorado']
    ], colWidths=[doc.width])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,-1), base_font),
        ('TOPPADDING', (0,0), (-1,0), 4),
        ('BOTTOMPADDING', (0,0), (-1,0), 2),
    ]))
    elements.append(sig_table)
    elements.append(Spacer(1, 12))

    # -------------------------------
    # Listado de estudiantes y estado de voto
    # -------------------------------
    elements.append(PageBreak())  
    elements.append(Paragraph("Listado de Estudiantes y Estado de Voto", styles['Heading2']))
    elements.append(Spacer(1, 6))

    padron = PadronElectoral.objects.filter(periodo=proceso.periodo).select_related('grado', 'paralelo')

    data_detalle = [['Cédula', 'Apellidos', 'Nombres', 'Grado-Paralelo', 'Votó']]

    for p in padron:
        voto = Voto.objects.filter(votante=p, proceso_electoral=proceso).first()
        data_detalle.append([
            p.cedula,
            p.apellidos,
            p.nombre,
            f"{p.grado.nombre} - {p.paralelo.nombre}",
            'Sí' if voto else 'No'
        ])

    tabla_detalle = Table(data_detalle, repeatRows=1, colWidths=[30*mm, 45*mm, 45*mm, 35*mm, 15*mm])
    tabla_detalle.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e2e8f0')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('FONTNAME', (0,0), (-1,0), base_font),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
        ('FONTNAME', (0,1), (-1,-1), base_font),
        ('FONTSIZE', (0,1), (-1,-1), 8),
    ]))
    elements.append(tabla_detalle)



    # -------------------------------
    # Generar y devolver el PDF
    # -------------------------------
    doc.build(elements)
    buffer.seek(0)
    nombre_archivo = f"Resultados_{proceso.nombre.replace(' ', '_')}_{datetime.now().date()}.pdf"
    return FileResponse(buffer, as_attachment=True, filename=nombre_archivo)