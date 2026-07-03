import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-clave'

DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    # 👉 Agrega la librería aquí arriba
    'admin_material',
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'apps.core',
    'apps.academico',
    'apps.personal',
    'apps.reportes',
    'apps.comunicaciones',
    'apps.asistencia',
    'debug_toolbar',  # 💥 Añadido para auditoría de rendimiento
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',  # 👈 requerido
    'django.middleware.common.CommonMiddleware',

    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',  # 👈 requerido
    'django.contrib.messages.middleware.MessageMiddleware',  # 👈 requerido

    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    'apps.core.middleware.NoCacheMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',  # 💥 Intercepta las peticiones para medirlas
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'db_torreblanca', # Ej: bd_torreblanca
        'USER': 'root', # Por lo general en XAMPP es root
        'PASSWORD': '', # Por lo general en XAMPP está en blanco
        'HOST': 'localhost',
        'PORT': '3306',
        
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    }
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',  # 👈 importante
                'django.contrib.auth.context_processors.auth',  # 👈 importante
                'django.contrib.messages.context_processors.messages',  # 👈 importante
                'apps.comunicaciones.context_processors.comunicado_pendiente_context',
                'apps.comunicaciones.context_processors.notificaciones_globales',
                'apps.academico.context_processors.institucion_global',
            ],
        },
    },
]

LOGIN_REDIRECT_URL = 'personal:enrutador_principal'
LOGOUT_REDIRECT_URL = '/login/'
LOGIN_URL = 'login'

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static') # 👉 Apunta a tu nueva carpeta static
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Opcional pero MUY recomendado para permitir iframes del mismo dominio
X_FRAME_OPTIONS = 'SAMEORIGIN'

LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Lima'

CSRF_TRUSTED_ORIGINS = [
    'https://*.ngrok-free.app',
    'https://*.ngrok.io',
]

SESSION_EXPIRE_AT_BROWSER_CLOSE = False 
SESSION_COOKIE_AGE = 1209600  # Duración por defecto si se mantiene iniciada: 2 semanas (en segundos)

if not DEBUG:
    # 1. Forzar HTTPS y HSTS (W008, W004)
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # Obliga a usar HTTPS por 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # 2. Cookies Encriptadas (W012, W016)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # 3. Protección Anti-Clickjacking (W019)
    X_FRAME_OPTIONS = 'DENY'

# 💥 IPs permitidas para ver el Debug Toolbar
#INTERNAL_IPS = [
#    '127.0.0.1',
#]