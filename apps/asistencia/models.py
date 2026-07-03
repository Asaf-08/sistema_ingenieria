from django.db import models
from django.utils import timezone
from apps.academico.models import Estudiante  
from apps.personal.models import Personal

class AbstractAsistencia(models.Model):
    """Modelo abstracto con los estados compartidos"""
    ESTADOS = [
        ('P', 'Presente (Temprano)'),
        ('T', 'Tarde'),
        ('J', 'Falta Justificada'),
        ('F', 'Falta'),
    ]
    # 💥 Optimizado: Las búsquedas de reportes siempre se filtran por fecha
    fecha = models.DateField(default=timezone.now, db_index=True)
    estado = models.CharField(max_length=1, choices=ESTADOS, default='F')

    class Meta:
        abstract = True

class AsistenciaPersonal(models.Model):
    personal = models.ForeignKey(Personal, on_delete=models.CASCADE, related_name='asistencias')
    # 💥 Optimizado: Para buscar rápidamente quién faltó un día específico
    fecha = models.DateField(db_index=True)
    hora_entrada = models.TimeField(null=True, blank=True)
    hora_salida = models.TimeField(null=True, blank=True)
    
    ESTADOS = [
        ('P', 'Puntual'),
        ('T', 'Tardanza'),
        ('F', 'Falta'),
        ('J', 'Justificada'), 
    ]
    # 💥 Optimizado: Para filtrar a todos los que llegaron tarde
    estado = models.CharField(max_length=1, choices=ESTADOS, default='F', db_index=True)
    
    justificacion = models.TextField(blank=True, null=True, help_text="Motivo de la tardanza o falta")
    
    TIPO_ACTIVIDAD = [
        ('REGULAR', 'Clase/Jornada Regular'),
        ('ASESORIA', 'Asesoría/Reunión'),
        ('OTRO', 'Otro')
    ]
    tipo_actividad = models.CharField(max_length=15, choices=TIPO_ACTIVIDAD, default='REGULAR')
    observaciones = models.TextField(blank=True, null=True, help_text="Observaciones (Opcional)")

    class Meta:
        unique_together = ('personal', 'fecha')
        verbose_name_plural = "Asistencias del Personal"

class AsistenciaEstudiante(AbstractAsistencia):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='asistencias')
    hora_registro = models.TimeField(null=True, blank=True)
    
    ESTADOS_ESTUDIANTE = [
        ('P', 'Presente'),
        ('T', 'Tardanza'),
        ('F', 'Falta'),
        ('J', 'Falta Justificada'),
    ]
    # 💥 Optimizado: Para contar rápidamente las faltas en el reporte cualitativo
    estado = models.CharField(max_length=1, choices=ESTADOS_ESTUDIANTE, default='P', db_index=True)
    justificacion = models.TextField(blank=True, null=True, help_text="Motivo de la falta o tardanza")
    observaciones = models.TextField(blank=True, null=True, help_text="Observaciones (Opcional)")
    
    class Meta:
        unique_together = ('estudiante', 'fecha')
        verbose_name_plural = "Asistencias de Estudiantes"