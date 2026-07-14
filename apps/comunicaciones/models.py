from django.utils import timezone
from django.db import models
from django.contrib.auth import get_user_model
import os
from apps.personal.models import Personal
from django.core.exceptions import ValidationError
from PIL import Image

User = get_user_model()

# ==========================================
# 🛡️ 1. EL CADENERO (Validador Global)
# ==========================================
def validar_peso_archivo(archivo):
    limite_mb = 5  # Máximo 5MB
    if archivo.size > limite_mb * 1024 * 1024:
        raise ValidationError(f"El archivo es muy pesado. El límite máximo es de {limite_mb}MB.")

# =========================================================
# SUBMÓDULO 1: AVISOS Y COMUNICADOS OFICIALES
# =========================================================

class Comunicado(models.Model):
    NIVELES_IMPORTANCIA = (
        ('NORMAL', 'Normal'),
        ('URGENTE', 'Urgente'),
    )
    
    AUDIENCIAS = (
        ('TODOS', 'Todo el Personal (General)'),
        ('DOCENTES', 'Todos los Docentes'),
        ('ADMINISTRATIVOS', 'Personal Administrativo'),
        ('PERSONALIZADO', 'Personalizado (Filtros Avanzados)...'),
    )

    titulo = models.CharField(max_length=200, verbose_name="Título del Comunicado")
    mensaje = models.TextField(verbose_name="Mensaje")
    importancia = models.CharField(max_length=20, choices=NIVELES_IMPORTANCIA, default='NORMAL', db_index=True)
    
    audiencia = models.CharField(max_length=20, choices=AUDIENCIAS, default='TODOS', db_index=True)
    destinatarios_especificos = models.ManyToManyField('personal.Personal', blank=True, related_name='comunicados_especificos')
    
    # 💥 Optimizado: Agregamos el validador de peso aquí
    archivo_adjunto = models.FileField(
        upload_to='comunicados/', 
        blank=True, 
        null=True, 
        verbose_name="Archivo Adjunto (Opcional)",
        validators=[validar_peso_archivo] 
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True, db_index=True)
    fecha_expiracion = models.DateTimeField(blank=True, null=True, help_text="Fecha en la que dejará de aparecer en el modal", db_index=True)
    creado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comunicados_creados')
    activo = models.BooleanField(default=True, verbose_name="¿Sigue Activo?", db_index=True)

    class Meta:
        verbose_name = "Comunicado Oficial"
        verbose_name_plural = "Comunicados Oficiales"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.titulo} - {self.get_importancia_display()}"
    
    # 💥 Optimizado: Compresor Automático de Imágenes
    def save(self, *args, **kwargs):
        # 1. Guardamos el registro en la BD y el archivo original en el disco
        super().save(*args, **kwargs)

        # 2. Si hay archivo, revisamos si es imagen para comprimirla
        if self.archivo_adjunto:
            extension = os.path.splitext(self.archivo_adjunto.name)[1].lower()
            if extension in ['.jpg', '.jpeg', '.png', '.webp']:
                try:
                    img = Image.open(self.archivo_adjunto.path)
                    # Si es mayor a 1080p, la redimensionamos
                    if img.height > 1080 or img.width > 1080:
                        img.thumbnail((1080, 1080))
                        # Sobrescribimos el archivo físico optimizándolo
                        img.save(self.archivo_adjunto.path, quality=85, optimize=True)
                except Exception as e:
                    print(f"Error al comprimir imagen del comunicado: {e}")

    @property
    def es_imagen(self):
        if self.archivo_adjunto:
            extension = os.path.splitext(self.archivo_adjunto.name)[1].lower()
            return extension in ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        return False

    @property
    def es_pdf(self):
        if self.archivo_adjunto:
            extension = os.path.splitext(self.archivo_adjunto.name)[1].lower()
            return extension == '.pdf'
        return False

    @property
    def estado_actual(self):
        if not self.activo:
            return 'Inactivo'
        if self.fecha_expiracion and self.fecha_expiracion < timezone.now():
            return 'Expirado'
        return 'Vigente'


class LecturaComunicado(models.Model):
    comunicado = models.ForeignKey(Comunicado, on_delete=models.CASCADE, related_name='lecturas')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comunicados_leidos')
    
    # 💥 Optimizado: Para saber rápido quién NO ha leído
    leido = models.BooleanField(default=False, db_index=True)
    fecha_lectura = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('comunicado', 'usuario')
        verbose_name = "Control de Lectura"
        verbose_name_plural = "Controles de Lectura"

    def __str__(self):
        estado = "Leído" if self.leido else "Pendiente"
        return f"{self.usuario.get_full_name()} - {self.comunicado.titulo} ({estado})"


# =========================================================
# SUBMÓDULO 2: ENTREGABLES Y EVIDENCIAS DE DOCENTES
# =========================================================

class Actividad(models.Model):
    titulo = models.CharField(max_length=200, verbose_name="Título de la Actividad/Entregable")
    descripcion = models.TextField(verbose_name="Instrucciones")
    formato_adjunto = models.FileField(upload_to='formatos_actividades/', blank=True, null=True, help_text="Ej: Plantilla en Word o PDF a llenar")
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    # 💥 Optimizado: Para el dashboard de pendientes de entregar
    fecha_limite = models.DateTimeField(verbose_name="Fecha Límite de Entrega", db_index=True)
    
    creado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='actividades_creadas')

    class Meta:
        verbose_name = "Actividad / Entregable"
        verbose_name_plural = "Actividades y Entregables"
        ordering = ['fecha_limite']

    def __str__(self):
        return self.titulo


class EvidenciaActividad(models.Model):
    ESTADOS_ENTREGA = (
        ('PENDIENTE', 'Pendiente'),
        ('ENTREGADO', 'Entregado'),
        ('REVISADO', 'Revisado por Coordinación'),
    )

    # Supongo que Actividad y Personal están importados arriba en tu archivo original
    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE, related_name='evidencias')
    personal = models.ForeignKey(Personal, on_delete=models.CASCADE, related_name='evidencias_subidas')
    
    # 💥 Optimizado: Agregamos el validador de peso aquí también
    archivo_evidencia = models.FileField(
        upload_to='evidencias_personal/', 
        blank=True, 
        null=True,
        validators=[validar_peso_archivo]
    )
    
    comentario_personal = models.TextField(blank=True, null=True, help_text="Nota opcional al entregar")
    estado = models.CharField(max_length=20, choices=ESTADOS_ENTREGA, default='PENDIENTE', db_index=True)
    fecha_entrega = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        unique_together = ('actividad', 'personal') 
        verbose_name = "Evidencia de Personal"
        verbose_name_plural = "Evidencias del Personal"

    def __str__(self):
        return f"Evidencia de {self.personal.nombres} {self.personal.apellidos} - {self.actividad.titulo}"

    # 💥 Optimizado: Compresor Automático de Imágenes
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.archivo_evidencia:
            extension = os.path.splitext(self.archivo_evidencia.name)[1].lower()
            if extension in ['.jpg', '.jpeg', '.png', '.webp']:
                try:
                    img = Image.open(self.archivo_evidencia.path)
                    if img.height > 1080 or img.width > 1080:
                        img.thumbnail((1080, 1080))
                        img.save(self.archivo_evidencia.path, quality=85, optimize=True)
                except Exception as e:
                    print(f"Error al comprimir evidencia: {e}")

class Notificacion(models.Model):
    TIPO_CHOICES = [
        ('INFO', 'Información'),
        ('ALERTA', 'Alerta / Acción Requerida'),
        ('EXITO', 'Éxito / Confirmación'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones')
    titulo = models.CharField(max_length=100)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='INFO')
    
    # 💥 Optimizado: Los context_processors calculan las leídas a cada segundo
    leida = models.BooleanField(default=False, db_index=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, db_index=True)
    enlace = models.CharField(max_length=200, blank=True, null=True, help_text="URL a donde ir al hacer clic (opcional)")

    class Meta:
        ordering = ['-fecha_creacion'] 

    def __str__(self):
        return f"[{self.tipo}] {self.titulo} - {self.usuario.username}"