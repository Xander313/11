from django.shortcuts import render, redirect
from django.contrib import messages
from .models import LogoConfig

def agregar_logo(request):
    config = LogoConfig.objects.first()
    logo_config = LogoConfig.objects.first()  # Para la barra de navegación
    return render(request, 'configuracion/configuracion.html', {'config': config, 'logo_config': logo_config})

def configurar_logo(request):
    config = LogoConfig.objects.first()
    logo_config = LogoConfig.objects.first()  # Para la barra de navegación

    if request.method == 'POST':
        logo_1 = request.FILES.get('logo_1')
        logo_2 = request.FILES.get('logo_2')
        iniciales = request.POST.get('iniciales')

        if config:
            if logo_1:
                config.logo_1 = logo_1
            if logo_2:
                config.logo_2 = logo_2
            config.iniciales = iniciales
            config.save()
        else:
            config = LogoConfig.objects.create(
                logo_1=logo_1,
                logo_2=logo_2,
                iniciales=iniciales
            )
        messages.success(request, 'Configuración guardada exitosamente.')
        return redirect('configurar_logo')

    return render(request, 'configuracion/configuracion.html', {'config': config, 'logo_config': logo_config})