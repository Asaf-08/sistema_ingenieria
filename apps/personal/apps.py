from django.apps import AppConfig
from django.db.models.signals import post_migrate

class PersonalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.personal'

    def ready(self):
        # Importamos las señales para que Django las monte en memoria
        import apps.personal.signals
        
        # 💥 OPTIMIZACIÓN SENIOR: Le decimos a Django que cree los roles 
        # ÚNICAMENTE después de que la base de datos haya sido migrada con éxito.
        post_migrate.connect(apps.personal.signals.crear_roles_maestros, sender=self)