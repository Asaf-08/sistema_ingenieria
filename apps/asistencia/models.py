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
    
    # 💥 NUEVO CAMPO: Para facilitar los reportes
    bimestre = models.CharField(
        max_length=3, 
        choices=[('I', 'Bimestre I'), ('II', 'Bimestre II'), ('III', 'Bimestre III'), ('IV', 'Bimestre IV')],
        default='I',
        db_index=True
    )
    
    fecha = models.DateField(default=timezone.now, db_index=True)
    estado = models.CharField(max_length=1, choices=ESTADOS, default='F')

    class Meta:
        abstract = True

class AsistenciaPersonal(models.Model):
    personal = models.ForeignKey(
        Personal,
        on_delete=models.CASCADE,
        related_name='asistencias',
        null=True,
        blank=True
    )
    # Para visitas o personal externo no registrado en la tabla Personal (Promotor, Supervisor, Instructor, etc.)
    nombre_externo = models.CharField(max_length=150, blank=True, null=True, verbose_name="Nombre (Personal Externo)")
    cargo_externo = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cargo / Motivo (Externo)")

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

    @property
    def es_externo(self):
        return self.personal_id is None

    @property
    def nombre_mostrado(self):
        if self.personal:
            return f"{self.personal.apellidos}, {self.personal.nombres}"
        return self.nombre_externo or "Personal Externo"

    @property
    def cargo_mostrado(self):
        if self.personal:
            return self.personal.get_cargo_display()
        return self.cargo_externo or "Visita / Externo"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['personal', 'fecha'],
                condition=models.Q(personal__isnull=False),
                name='unique_personal_fecha_no_nulo'
            )
        ]
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
    estado = models.CharField(max_length=1, choices=ESTADOS_ESTUDIANTE, default='P', db_index=True)
    justificacion = models.TextField(blank=True, null=True, help_text="Motivo de la falta o tardanza")
    observaciones = models.TextField(blank=True, null=True, help_text="Observaciones (Opcional)")
    
    class Meta:
        # 💥 EL SECRETO: Mantenemos solo el estudiante y la fecha
        # Así aseguramos que solo exista UN marcaje por día en la vida real
        unique_together = ('estudiante', 'fecha')
        verbose_name_plural = "Asistencias de Estudiantes"