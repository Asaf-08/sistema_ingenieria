import os
import dj_database_url
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-clave'

# Railway enviará una variable diciendo "DEBUG=False" cuando estemos en producción. 
# Si no la envía (como en tu PC), seguirá en 'True'.
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# Permitimos todos los dominios por ahora para que la URL gratuita de Railway funcione
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
    
    'debug_toolbar',  # 💥 Añadido para auditoría de rendimiento
    'storages', # 💥 Nueva: Para hablar con AWS

    'apps.core',
    'apps.academico',
    'apps.personal',
    'apps.reportes',
    'apps.comunicaciones',
    'apps.asistencia',

    'django_cleanup.apps.CleanupConfig', # 💥 Nueva: El conserje (SIEMPRE AL FINAL)
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # 💥 AÑADIDO: Entrega CSS/JS a máxima velocidad
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

# 💥 NUEVO: Intercepta la base de datos si estamos en Railway
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES['default'] = dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        ssl_require=True
    )

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

# 💥 NUEVO: Rutas de producción para Railway
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# =========================================================
# CONFIGURACIÓN DE ARCHIVOS MULTIMEDIA (LOCAL VS AWS S3)
# =========================================================
USE_S3 = os.environ.get('USE_S3', 'False') == 'True'

if USE_S3:
    # 💥 Entorno de Producción (Nube)
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME')
    
    AWS_S3_FILE_OVERWRITE = False # Evita que archivos con el mismo nombre se chanquen
    AWS_DEFAULT_ACL = None 
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    
    # Le decimos a Django que mande los subidas (media) a S3
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
else:
    # 💥 Entorno Local (Tu PC / XAMPP)
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

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

# ==========================================
# CONFIGURACIONES DE SEGURIDAD PARA PRODUCCIÓN (RAILWAY)
# ==========================================

# 1. Romper el Bucle Infinito (Entender el proxy de Railway)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# 2. Confiar en los dominios de Railway para evitar errores CSRF 403 al loguearse
CSRF_TRUSTED_ORIGINS = ['https://*.up.railway.app']

# ==========================================
# CONFIGURACIÓN DEL MICROSERVICIO DE WHATSAPP
# ==========================================
# Reemplaza esto con la URL real que te dio Railway
WHATSAPP_BOT_URL = 'https://botcomunicacion-ws.up.railway.app'

# ==========================================
# 🔐 SEGURIDAD DE SESIONES Y COOKIES
# ==========================================

# 1. Tiempo de inactividad (Ejemplo: 30 minutos = 1800 segundos)
# Si el usuario no hace clic en nada por 30 minutos, la sesión muere.
SESSION_COOKIE_AGE = 1800 

# 2. Renovar el tiempo con cada acción
# Cada vez que el profesor guarde una nota o cambie de página, el reloj de 30 minutos vuelve a cero.
SESSION_SAVE_EVERY_REQUEST = True 

# 3. Muerte al cerrar el navegador (Vital para cabinas o sala de profes)
# Si el profe simplemente le da a la "X" roja del navegador sin cerrar sesión,
# el alumno no podrá presionar "Ctrl + Shift + T" para revivir la pestaña.
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# 💥 IPs permitidas para ver el Debug Toolbar
#INTERNAL_IPS = [
#    '127.0.0.1',
#]

