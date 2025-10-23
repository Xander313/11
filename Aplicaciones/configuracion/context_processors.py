from .models import LogoConfig

def logo_config(request):
    return {'logo_config': LogoConfig.objects.first()}