from pathlib import Path
import os
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-0drj0i+d)l6_40jeqi(k-$*o)4&q0=2z34v9@9@3u%e^y(u@^y'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['escuelariobamba.com', 'www.escuelariobamba.com', '127.0.0.1', 'localhost', "*"]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'Aplicaciones.administracion',
    'Aplicaciones.elecciones',
    'Aplicaciones.padron',
    'Aplicaciones.votacion',
    'Aplicaciones.usuarios',
    'Aplicaciones.periodo',
    'Aplicaciones.autenticacion',
    'Aplicaciones.configuracion',
    'Aplicaciones.resultados',
    'Aplicaciones.noticias',
    
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sistema_voto_ue_riobamba.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR / 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'Aplicaciones.configuracion.context_processors.logo_config',  # Añadir el context processor aquí
            ],
        },
    },
]

WSGI_APPLICATION = 'sistema_voto_ue_riobamba.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_votaciones_riobamba.db',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'es-ec'

TIME_ZONE = 'America/Guayaquil'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

# Configuración de archivos estáticos
STATIC_URL = '/static/'

# Directorio donde se recopilarán los archivos estáticos para producción
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Directorios donde Django buscará archivos estáticos adicionales
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'sistema_voto_ue_riobamba', 'static'),
    os.path.join(BASE_DIR, 'Aplicaciones', 'administracion', 'static'),
    os.path.join(BASE_DIR, 'Aplicaciones', 'padron', 'static'),
]

# Ignorar archivos .map en desarrollo
STATICFILES_IGNORE_PATTERNS = [
    '*.map',
]

#MEDIA PARA IMAGENES
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR / 'media')

#MEDIA PARA IMAGENES

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Configuración para el envío de correos en desarrollo

AUTH_USER_MODEL = 'usuarios.Usuarios'  # Esto debe estar definido

##CONFIGURACION PARA ENVIO DE CORREOS ELECTRONICOS CON EL CORREO PERSONAL DE GMAIL
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'cloudgrup31@gmail.com'
EMAIL_HOST_PASSWORD = 'szdn snln hvly jivx'
#CONFIGURACION DE CORREO ELECTRONICO


DEFAULT_FROM_EMAIL = 'Sistema de Votación UE DEL MILENIO 11 DE NOVIEMBRE <cloudgrup31@gmail.com>'

# Configuración del sitio
#SITE_URL = 'https://escuelariobamba.com'

# Configuración de seguridad para HTTPS en producción

