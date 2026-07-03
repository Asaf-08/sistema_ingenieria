from django.contrib import admin
from .models import Comunicado, LecturaComunicado, Actividad, EvidenciaActividad

@admin.register(Comunicado)
class ComunicadoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'importancia', 'creado_por', 'fecha_creacion')
    list_filter = ('importancia', 'fecha_creacion')
    search_fields = ('titulo', 'mensaje')

@admin.register(LecturaComunicado)
class LecturaComunicadoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'comunicado', 'leido', 'fecha_lectura')
    list_filter = ('leido', 'fecha_lectura')

@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'creado_por', 'fecha_limite')
    search_fields = ('titulo', 'descripcion')

@admin.register(EvidenciaActividad)
class EvidenciaActividadAdmin(admin.ModelAdmin):
    list_display = ('actividad', 'personal', 'estado', 'fecha_entrega')
    list_filter = ('estado',)