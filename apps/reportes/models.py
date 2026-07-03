from django.db import models
from django.contrib.auth import get_user_model
from apps.academico.models import Aula, Curso, PeriodoLectivo

User = get_user_model()

class HistorialReporte(models.Model):
    TIPOS_REPORTE = [
        ('LIBRETA_AULA', 'Libretas de Aula (Excel)'),
        ('MATRIZ_CURSO', 'Matriz Oficial de Curso (Excel)'),
        ('AGENDA_TICKETS', 'Tickets de Agenda Semanal (Excel)'),
        ('DIAGNOSTICO_IA', 'Diagnóstico General IA (PDF)')
    ]

    solicitado_por = models.ForeignKey(User, on_delete=models.CASCADE)
    tipo_reporte = models.CharField(max_length=50, choices=TIPOS_REPORTE, db_index=True)
    
    # Referencias opcionales (dependiendo de qué reporte se generó)
    aula = models.ForeignKey(Aula, on_delete=models.SET_NULL, null=True, blank=True)
    curso = models.ForeignKey(Curso, on_delete=models.SET_NULL, null=True, blank=True)
    periodo = models.ForeignKey(PeriodoLectivo, on_delete=models.SET_NULL, null=True, blank=True)
    
    # El archivo generado
    archivo_generado = models.FileField(upload_to='reportes_generados/')
    fecha_generacion = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Tiempo que le tomó al servidor generarlo (Excelente métrica para tu tesis)
    tiempo_procesamiento_segundos = models.FloatField(default=0.0)

    class Meta:
        verbose_name = "Historial de Reporte"
        verbose_name_plural = "Historial de Reportes"
        ordering = ['-fecha_generacion']

    def __str__(self):
        return f"{self.get_tipo_reporte_display()} - {self.fecha_generacion.strftime('%d/%m/%Y %H:%M')}"