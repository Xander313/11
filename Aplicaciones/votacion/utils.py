import qrcode
import hashlib
import os
from io import BytesIO

from django.core.files import File
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import datetime
from premailer import transform

def generar_codigo_verificacion(voto):
    """
    Genera un código de verificación único para el voto
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
    texto = f"{voto.id}-{voto.votante.cedula}-{timestamp}"
    return hashlib.sha256(texto.encode()).hexdigest()

def generar_carnet_votacion(voto):
    """
    Genera un carnet de votación para un voto emitido (usa el logo institucional en lugar de un código QR)
    """
    from .models import CarnetVotacion
    from django.core.files.base import ContentFile
    from django.conf import settings
    import base64
    import os

    # Generar código de verificación
    codigo_verificacion = generar_codigo_verificacion(voto)

    # Crear el registro del carnet
    carnet = CarnetVotacion(
        voto=voto,
        codigo_verificacion=codigo_verificacion,
        nombre_completo=f"{voto.votante.nombre} {voto.votante.apellidos}",
        cedula=voto.votante.cedula,
        proceso_electoral=str(voto.proceso_electoral),
        fecha_votacion=voto.fecha_voto
    )

    # Cargar el logo institucional como imagen base64
    logo_path = "/home/axel/Escritorio/11/sistema_voto_ue_riobamba/static/images/logo1.png"
    /home/axel/Escritorio/11/sistema_voto_ue_riobamba/static/images/logo1.png
    try:
        with open(logo_path, "rb") as logo_file:
            logo_data = logo_file.read()
            logo_base64 = base64.b64encode(logo_data).decode("utf-8")
            carnet.codigo_qr = f"data:image/png;base64,{logo_base64}"
            print(f"✅ Logo institucional cargado desde: {logo_path}")
    except Exception as e:
        print(f"⚠️ Error al cargar el logo institucional: {e}")
        carnet.codigo_qr = None

    # Guardar el carnet
    carnet.save()

    # Enviar comprobante por correo electrónico
    enviar_comprobante_email(carnet)

    return carnet


"""
def enviar_comprobante_email(carnet, request=None):
    
    Envía el comprobante de votación por correo electrónico al votante
    
    try:
        from django.core.mail import EmailMultiAlternatives
        from django.conf import settings
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        from email.mime.image import MIMEImage
        import base64
        import io
        from PIL import Image
        
        # Obtener el correo del votante
        email_destino = carnet.voto.votante.correo
        
        if not email_destino:
            print("No se encontró correo electrónico para el votante")
            return False
            
        print(f'=== ENVIANDO COMPROBANTE A: {email_destino} ===')
        
        # DEBUG: Verificar si el código QR existe
        if not carnet.codigo_qr:
            print("ERROR: El código QR no existe en el carnet")
            # Regenerar el QR si no existe
            # Obtener el dominio actual
            domain = getattr(settings, 'SITE_URL', 'http://localhost:8000')
            # Crear la URL de verificación
            from django.urls import reverse
            verification_url = f"{domain}{reverse('votacion:verificar_carnet', kwargs={'codigo_verificacion': carnet.codigo_verificacion})}"
            
            # Regenerar el QR
            print(f"Regenerando QR para URL: {verification_url}")
            import qrcode
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(verification_url)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            qr_img.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            carnet.codigo_qr = f"data:image/png;base64,{qr_base64}"
            carnet.save()
            print("QR regenerado exitosamente")
        else:
            # Verificar que el código QR tiene el formato correcto
            print(f"Código QR encontrado con longitud: {len(carnet.codigo_qr)} caracteres")
            if not carnet.codigo_qr.startswith('data:image/'):
                print("ERROR: El código QR no tiene el formato correcto de data:image")
                # Si no comienza con data:image, es posible que falte el prefijo
                if not carnet.codigo_qr.startswith('data:'):
                    carnet.codigo_qr = f"data:image/png;base64,{carnet.codigo_qr}"
                    carnet.save()
                    print("Formato QR corregido")
        

        
        # Obtener la configuración del logo
        from Aplicaciones.configuracion.models import LogoConfig
        logo_config = LogoConfig.objects.first()
        
        # Obtener el dominio para construir URLs absolutas
        dominio = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        
        # Renderizar el template HTML del correo
        context = {
            'carnet': carnet,
            'logo_config': logo_config,
            'dominio': dominio,
            'fecha_emision': carnet.fecha_votacion,
            'qr_code': carnet.codigo_qr,  # Asegurar que el QR esté disponible en el contexto
        }
        
        # Renderizar el contenido del correo
        html_content = render_to_string('votacion/email_comprobante.html', context)
        
        # Crear versión de texto plano
        text_content = strip_tags(html_content)
        
        # Configurar el asunto
        subject = f'Comprobante de Votación - {carnet.proceso_electoral}'
        
        # Adjuntar QR explícitamente como imagen embebida
        if carnet.codigo_qr and carnet.codigo_qr.startswith('data:image/png;base64,'):
            try:
                # Extraer datos de base64
                qr_data = carnet.codigo_qr.split('base64,')[1]
                qr_binary = base64.b64decode(qr_data)
                
                # Crear y adjuntar la imagen
                qr_image = MIMEImage(qr_binary)
                qr_image.add_header('Content-ID', '<codigo_qr>')
                
                # Modificar el HTML para usar la imagen embebida en lugar de base64
                html_content = html_content.replace(
                    f'src="{carnet.codigo_qr}"', 
                    'src="cid:codigo_qr"'
                )
                print("QR adjuntado como imagen embebida")
            except Exception as e:
                print(f"Error al procesar el QR para email: {str(e)}")
        else:
            print(f"ERROR: Formato incorrecto del QR o QR no encontrado")
        
        # Crear el mensaje de correo
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,  # Usar el remitente configurado en settings.py
            to=[email_destino],
        )
        
        # Adjuntar la versión HTML
        email.attach_alternative(html_content, "text/html")
        
        # Adjuntar el logo si existe
        if logo_config and logo_config.logo_1:
            try:
                logo_path = logo_config.logo_1.path
                with open(logo_path, 'rb') as f:
                    logo = MIMEImage(f.read())
                    logo.add_header('Content-ID', '<logo_institucional>')
                    email.attach(logo)
            except Exception as e:
                print(f'Error al adjuntar el logo: {str(e)}')
                
        # Adjuntar el QR como imagen embebida (si se procesó correctamente)
        if 'qr_image' in locals():
            email.attach(qr_image)
            
        # DEBUG: Imprimir un fragmento del HTML final
        print(f"Fragmento HTML del correo (buscando QR): {html_content.find('codigo_qr')}")
        
        # Enviar el correo
        email.send(fail_silently=False)
        
        print('Correo enviado exitosamente')
        return True
        
    except Exception as e:
        import traceback
        print('=== ERROR AL ENVIAR CORREO ===')
        print(f'Tipo de error: {type(e).__name__}')
        print(f'Mensaje de error: {str(e)}')
        print('Traceback:')
        print(traceback.format_exc())
        print('=== FIN DEL ERROR ===')
        return False
"""

def enviar_comprobante_email(carnet, request=None):
    """
    Envía el comprobante de votación por correo electrónico al votante
    """
    try:
        from django.core.mail import EmailMultiAlternatives
        from django.conf import settings
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        from email.mime.image import MIMEImage
        import base64

        # Obtener el correo del votante
        email_destino = carnet.voto.votante.correo
        if not email_destino:
            print("No se encontró correo electrónico para el votante")
            return False

        print(f'=== ENVIANDO COMPROBANTE A: {email_destino} ===')

        # Obtener la configuración del logo institucional adicional
        from Aplicaciones.configuracion.models import LogoConfig
        logo_config = LogoConfig.objects.first()

        # Obtener el dominio para construir URLs absolutas
        dominio = getattr(settings, 'SITE_URL', 'http://localhost:8000')

        # Preparar contexto para el template
        context = {
            'carnet': carnet,
            'logo_config': logo_config,
            'dominio': dominio,
            'fecha_emision': carnet.fecha_votacion,
            'logo_base64': carnet.codigo_qr,  # ahora contiene el logo embebido
        }

        # Renderizar el contenido HTML del correo
        html_content = render_to_string('votacion/email_comprobante.html', context)
        text_content = strip_tags(html_content)
        subject = f'Comprobante de Votación - {carnet.proceso_electoral}'

        # Crear el mensaje de correo
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email_destino],
        )
        email.attach_alternative(html_content, "text/html")

        # Adjuntar el logo embebido desde carnet.codigo_qr
        if carnet.codigo_qr and carnet.codigo_qr.startswith('data:image/png;base64,'):
            try:
                logo_data = carnet.codigo_qr.split('base64,')[1]
                logo_binary = base64.b64decode(logo_data)
                logo_image = MIMEImage(logo_binary)
                logo_image.add_header('Content-ID', '<logo_embebido>')
                email.attach(logo_image)

                # Reemplazar en el HTML para usar imagen embebida
                html_content = html_content.replace(
                    f'src="{carnet.codigo_qr}"',
                    'src="cid:logo_embebido"'
                )
                print("✅ Logo institucional embebido en el correo")
            except Exception as e:
                print(f"⚠️ Error al procesar el logo embebido: {str(e)}")
        else:
            print("⚠️ El logo embebido no tiene formato base64 válido")

        # Adjuntar el logo institucional desde configuración (si existe)
        if logo_config and logo_config.logo_1:
            try:
                logo_path = logo_config.logo_1.path
                with open(logo_path, 'rb') as f:
                    logo = MIMEImage(f.read())
                    logo.add_header('Content-ID', '<logo_institucional>')
                    email.attach(logo)
            except Exception as e:
                print(f'⚠️ Error al adjuntar el logo institucional desde configuración: {str(e)}')

        # Enviar el correo
        email.send(fail_silently=False)
        print('📩 Correo enviado exitosamente')
        return True

    except Exception as e:
        import traceback
        print('=== ERROR AL ENVIAR CORREO ===')
        print(f'Tipo de error: {type(e).__name__}')
        print(f'Mensaje de error: {str(e)}')
        print('Traceback:')
        print(traceback.format_exc())
        print('=== FIN DEL ERROR ===')
        return False
