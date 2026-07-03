import os

from django.apps import AppConfig


class ComunicacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.comunicaciones'
    verbose_name = 'Gestión de Comunicaciones'

    def ready(self):
        # Evitamos que el reloj se inicie dos veces cuando Django recarga en desarrollo
        if os.environ.get('RUN_MAIN'):
            from . import tareas_programadas
            tareas_programadas.iniciar_reloj()