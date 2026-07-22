from datetime import time

from django.db import models
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from apps.personal.models import Personal
from django.core.exceptions import ValidationError


class PeriodoLectivo(models.Model):
    BIMESTRES = [
        ('I', 'Bimestre I'),
        ('II', 'Bimestre II'),
        ('III', 'Bimestre III'),
        ('IV', 'Bimestre IV'),
    ]
    # Guardamos solo el número. unique=True evita que creen dos veces el 2026
    anio = models.PositiveIntegerField(unique=True, verbose_name="Año Escolar") 
    activo = models.BooleanField(default=True, db_index=True) # 💥 Optimizado
    
    bimestre_actual = models.CharField(max_length=5, choices=BIMESTRES, default='I')
    
    pausar_notificaciones = models.BooleanField(
        default=False, 
        verbose_name="Pausar alertas automáticas (Feriados/Vacaciones)"
    )

    def __str__(self):
        # Aquí lo "maquillamos" para que en los selects y en el panel diga "Año Escolar 2026"
        return f"Año Escolar {self.anio}"

    class Meta:
        verbose_name = "Periodo Lectivo"
        verbose_name_plural = "Periodos Lectivos"
        ordering = ['-anio'] # Siempre ordenará del más reciente al más antiguo matemáticamente


class Aula(models.Model):
    """
    Reemplaza a las tablas separadas de grados y secciones de tu SQL.
    Aquí registramos las aulas físicas reales (Ej: 1er Grado A, 3 Años Única).
    """

    NIVELES = [
        ('Inicial', 'Inicial'),
        ('Primaria', 'Primaria'),
        ('Secundaria', 'Secundaria'),
    ]

    GRADOS = [
        # Inicial
        ('3 Años', '3 Años'), ('4 Años', '4 Años'), ('5 Años', '5 Años'),
        # Primaria
        ('1er Grado', '1er Grado'), ('2do Grado', '2do Grado'), ('3er Grado', '3er Grado'),
        ('4to Grado', '4to Grado'), ('5to Grado', '5to Grado'), ('6to Grado', '6to Grado'),
        # Secundaria
        ('1er Año', '1er Año'), ('2do Año', '2do Año'), ('3er Año', '3er Año'),
        ('4to Año', '4to Año'), ('5to Año', '5to Año'),
    ]

    SECCIONES = [('A', 'A'), ('B', 'B'), ('C', 'C')]

    nivel = models.CharField(max_length=20, choices=NIVELES)
    grado = models.CharField(max_length=50, choices=GRADOS, verbose_name="Grado/Año")
    seccion = models.CharField(max_length=10, choices=SECCIONES)
    # ... resto de campos
    denominacion = models.CharField(max_length=100, blank=True, null=True, help_text="Ej: Prototipo, Emprendedores")
    # En la clase Aula (apps/academico/models.py)
    tutor = models.ForeignKey(Personal, limit_choices_to={'cargo': 'DOC'}, on_delete=models.SET_NULL, null=True, blank=True, related_name='aulas_tutoradas')
    
    google_sheet_id = models.CharField(
        max_length=150, 
        blank=True, 
        null=True, 
        help_text="Pegue aquí el ID del Excel de Google Drive"
    )

    class Meta:
        verbose_name = "Aula"
        verbose_name_plural = "Aulas"
        unique_together = ('grado', 'nivel', 'seccion') 

    def __str__(self):
        if self.denominacion:
            return f'{self.grado} "{self.denominacion}" de {self.nivel} - Secc. {self.seccion}'
        return f"{self.grado} de {self.nivel} - Secc. {self.seccion}"


class Estudiante(models.Model):
    """
    Basado en tu tabla 'alumnos', pero adaptado a Django y relacionado directamente con el Aula.
    """
    ESTADOS = [
        ('Activo', 'Activo'),
        ('Retirado', 'Retirado'),
        ('Suspendido', 'Suspendido'),
    ]

    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100, db_index=True) # 💥 Optimizado para ordenamiento
    dni = models.CharField(max_length=8, unique=True, verbose_name="DNI")
    
    # Datos de contacto rápidos
    telefono_apoderado = models.CharField(max_length=15, blank=True, null=True, verbose_name="Teléfono del Apoderado")
    direccion = models.CharField(max_length=200, blank=True, null=True)
    
    # Auditoría (Lo que tenías como estado y fecha_registro en tu SQL)
    estado = models.CharField(max_length=15, choices=ESTADOS, default='Activo', db_index=True) # 💥 Optimizado para filtros
    fecha_registro = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Estudiante"
        verbose_name_plural = "Estudiantes"
        ordering = ['apellidos', 'nombres'] # Para que en las tablas siempre salgan en orden alfabético

    def __str__(self):
        return f"{self.apellidos}, {self.nombres}"
    
class Curso(models.Model):
    # 💥 LISTA DE ÁREAS BASADA EN EL FORMATO DEL COLEGIO
    AREAS_ACADEMICAS = [
        # --- ÁREAS DE PRIMARIA / SECUNDARIA ---
        ('MATEMATICA', 'Matemática'),
        ('COMUNICACION', 'Comunicación'),
        ('PERSONAL SOCIAL', 'Personal Social'),
        ('CIENCIA Y TECNOLOGIA', 'Ciencia y Tecnología'),
        ('CIENCIAS SOCIALES', 'Ciencias Sociales'),
        ('DPCC - ORATORIA', 'Desarrollo Personal, Ciudadanía y Cívica - Oratoria'),
        
        ('ARTE, CULTURA Y DANZA', 'Arte, Cultura y Danza'),
        ('EDUCACION PARA EL TRABAJO - COMPUTACION', 'Educación para el Trabajo - Computación'),
        ('EDUCACION RELIGIOSA - PSICOLOGIA', 'Educación Religiosa - Psicología'),

        # --- ÁREAS EXCLUSIVAS DE INICIAL ---
        ('PSICOMOTRICIDAD', 'Psicomotriz (Ed. Fisica)'),

        # --- CURSOS INDEPENDIENTES (Áreas Propias) ---
        ('ARTE', 'Arte y Cultura'),
        ('RELIGION', 'Religión'),
        ('EDUCACION FISICA', 'Educación Física'),
        ('TALLERES', 'Talleres'),
    ]

    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Curso")
    
    # 💥 NUEVO CAMPO ESTRATÉGICO
    # Aumentamos el max_length a 60 para que quepan las opciones de secundaria
    area = models.CharField(max_length=60, choices=AREAS_ACADEMICAS, default='COMUNICACION', verbose_name="Área Académica", db_index=True) # 💥
    
    descripcion = models.TextField(blank=True, null=True, help_text="Opcional")
    activo = models.BooleanField(default=True, verbose_name="¿Curso Activo?", db_index=True) # 💥

    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        # Ordenamos primero por área y luego alfabéticamente
        ordering = ['area', 'nombre']

class AsignacionAcademica(models.Model):
    personal = models.ForeignKey(Personal, limit_choices_to={'cargo': 'DOC'}, on_delete=models.CASCADE, related_name='asignaciones')
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='asignaciones')
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE, related_name='asignaciones')
    periodo = models.ForeignKey(PeriodoLectivo, on_delete=models.CASCADE, related_name='asignaciones')
    
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.curso.nombre} - {self.aula} ({self.personal.apellidos})"

    class Meta:
        verbose_name = "Asignación Académica"
        verbose_name_plural = "Asignaciones Académicas"
        # REGLA SENIOR: Un mismo curso en una misma aula en el mismo año, 
        # solo puede tener asignado un profesor. Esto evita registros duplicados.
        unique_together = ['curso', 'aula', 'periodo']

class Matricula(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE)
    periodo = models.ForeignKey(PeriodoLectivo, on_delete=models.CASCADE)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['estudiante', 'periodo'] # Un alumno no puede estar en dos salones el mismo año
        

# ==========================================
# MÓDULO DE EVALUACIONES Y NOTAS (EL MATA-EXCEL)
# ==========================================

class Evaluacion(models.Model):
    TIPOS = [
        ('DESAFIO', 'Desafío Diario'),
        ('MENSUAL', 'Control de Calidad (Examen Mensual)'),
        ('BIMESTRAL', 'ISO Ingeniería (Examen Bimestral)'),
        ('SIMULACRO', 'Concurso de Aptitud (Simulacro)'),
        ('CUADERNO', 'Revisión de Cuaderno'), # 💥 Separado
        ('LIBRO', 'Revisión de Libro'),       # 💥 Nuevo
    ]
    
    # Añadimos los bimestres
    BIMESTRES = [
        ('I', 'Bimestre I'),
        ('II', 'Bimestre II'),
        ('III', 'Bimestre III'),
        ('IV', 'Bimestre IV'),
    ]

    asignacion = models.ForeignKey(AsignacionAcademica, on_delete=models.CASCADE, related_name='evaluaciones')
    tipo = models.CharField(max_length=20, choices=TIPOS, db_index=True) # 💥
    bimestre = models.CharField(max_length=5, choices=BIMESTRES, default='I', db_index=True) # 💥
    nombre = models.CharField(max_length=100) 
    fecha = models.DateField(auto_now_add=True)


class Nota(models.Model):
    # La nota cruza al Alumno (Matricula) con el Examen (Evaluacion)
    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE, related_name='notas')
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.CASCADE, related_name='notas')
    
    # Guardamos la nota. Puede ser null/blank si el alumno faltó al examen
    valor = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"{self.matricula.estudiante.apellidos} - {self.valor}"

    class Meta:
        verbose_name = "Nota"
        verbose_name_plural = "Notas"
        # Un alumno no puede tener dos notas distintas en un mismo examen exacto
        unique_together = ['matricula', 'evaluacion']


class EvaluacionActitudinal(models.Model):
    """
    Este modelo es exclusivo para los Tutores. 
    Reemplaza la parte del Excel donde califican Valores y Disciplina.
    """
    BIMESTRES = [
        ('I', 'Bimestre I'),
        ('II', 'Bimestre II'),
        ('III', 'Bimestre III'),
        ('IV', 'Bimestre IV'),
    ]

    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE, related_name='actitudinales')
    
    # 💥 CAMBIO A BI-MESTRAL: Restringido a las 4 opciones oficiales
    bimestre = models.CharField(max_length=5, choices=BIMESTRES, default='I', verbose_name="Bimestre Evaluado", db_index=True) # 💥
    
    # Criterios del colegio (Por defecto asumo que se califica sobre 20)
    puntualidad = models.IntegerField(default=20)
    presentacion = models.IntegerField(default=20)
    cuidado_patrimonio = models.IntegerField(default=20)
    orden_limpieza = models.IntegerField(default=20)
    respeto_normas = models.IntegerField(default=20)
    
    recomendacion_ia = models.TextField(blank=True, null=True, help_text="Almacena las 4 recomendaciones generadas por Gemini en formato JSON.")
    
    @property
    def promedio_actitudinal(self):
        # Python calcula el promedio automáticamente
        suma = self.puntualidad + self.presentacion + self.cuidado_patrimonio + self.orden_limpieza + self.respeto_normas
        return suma / 5

    class Meta:
        verbose_name = "Evaluación Actitudinal"
        verbose_name_plural = "Evaluaciones Actitudinales"
        # 💥 REGLA ACTUALIZADA: Un alumno solo tiene una evaluación de conducta por bimestre
        unique_together = ['matricula', 'bimestre']

class SolicitudImpresion(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente de Revisión'),
        ('LISTO', 'Listo para Recoger'),
        ('ENTREGADO', 'Entregado al Docente'),
    ]
    TEMAS = [
        ('TEMA_1', 'Tema 1'),
        ('TEMA_2', 'Tema 2'),
        ('TEMA_3', 'Tema 3'),
        ('TEMA_4', 'Tema 4'),
        ('TEMA_5', 'Tema 5'),
        ('TEMA_6', 'Tema 6'),
        ('ASESORIA', 'Asesorías'),
        ('REPASO', 'Repaso / Adicional'),
    ]

    personal = models.ForeignKey(Personal, limit_choices_to={'cargo': 'DOC'}, on_delete=models.CASCADE, related_name='solicitudes', null=True, blank=True)
    asignacion = models.ForeignKey('AsignacionAcademica', on_delete=models.CASCADE)
    
    # Datos automáticos y de organización
    bimestre = models.CharField(max_length=5, default='I')
    tema = models.CharField(max_length=20, choices=TEMAS, default='TEMA_1')
    instrucciones = models.TextField(null=True, blank=True)
    
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE', db_index=True) # 💥
    fecha_subida = models.DateTimeField(auto_now_add=True, db_index=True) # 💥

    class Meta:
        verbose_name = "Solicitud de Impresión"
        verbose_name_plural = "Solicitudes de Impresión"
        ordering = ['-fecha_subida']

    @property
    def puede_editarse(self):
        # Solo se puede borrar/editar si la asistente aún no lo ha tocado
        return self.estado == 'PENDIENTE'

    def obtener_total_alumnos(self):
        """Calcula cuántos alumnos matriculados hay en el aula de esta solicitud"""
        from apps.academico.models import Matricula # Evita errores de importación circular
        total = Matricula.objects.filter(
            aula=self.asignacion.aula,
            periodo=self.asignacion.periodo
        ).count()
        
        return total

class ArchivoMaterial(models.Model):
    TIPOS = [
        ('SESION', 'Sesión de Aprendizaje'),
        ('FICHA', 'Ficha Aplicativa'),
        ('DESAFIO', 'Desafío Diario'),
        ('CALIDAD', 'Control de Calidad (Mensual)'),
        ('ISO', 'Examen ISO (Bimestral)'),
        ('ADICIONAL', 'Material Adicional'),
    ]
    # Aquí es donde fallaba porque había dos SolicitudImpresion arriba
    solicitud = models.ForeignKey(SolicitudImpresion, on_delete=models.CASCADE, related_name='archivos')
    tipo = models.CharField(max_length=20, choices=TIPOS)
    archivo = models.FileField(upload_to='materiales/%Y/%m/') 
    
    class Meta:
        verbose_name = "Archivo de Material"


class MaterialInstitucional(models.Model):
    """ Repositorio oficial gestionado por las Coordinadoras """
    CATEGORIAS = [
        ('FORMATO', 'Formatos y Plantillas'),
        ('AULA', 'Ambientación de Aula (Fotos Modelo)'),
        ('EVALUACION', 'Modelos de Evaluación'),
        ('GUIA', 'Guías y Manuales'),
    ]
    
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True, help_text="Instrucciones breves sobre este material.")
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='FORMATO')
    archivo = models.FileField(upload_to='materiales_coordinacion/', help_text="Sube un PDF, Word, Excel o Imagen.")
    
    # Auditoría
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    autor = models.ForeignKey(Personal, on_delete=models.CASCADE, related_name='materiales_publicados')

    class Meta:
        verbose_name = "Material Institucional"
        verbose_name_plural = "Materiales Institucionales"
        ordering = ['-fecha_publicacion']

    def __str__(self):
        return f"{self.get_categoria_display()} - {self.titulo}"


class EvidenciaDocente(models.Model):
    """ Entregas que hacen los tutores/docentes para ser revisadas """
    ESTADOS = [
        ('PENDIENTE', 'Pendiente de Revisión'),
        ('APROBADO', 'Aprobado'),
        ('OBSERVADO', 'Observado / Requiere Corrección'),
    ]
    
    titulo = models.CharField(max_length=200, help_text="Ej: Fotos del Periódico Mural de Marzo, Registro Auxiliar Semanal")
    descripcion = models.TextField(blank=True, null=True)
    archivo_evidencia = models.FileField(upload_to='evidencias_docentes/', help_text="Sube la evidencia (PDF, Imagen, etc.)")
    
    # Relaciones
    docente = models.ForeignKey(Personal, on_delete=models.CASCADE, related_name='evidencias_enviadas')
    fecha_envio = models.DateTimeField(auto_now_add=True, db_index=True) # 💥
    
    # Retroalimentación (Se llena cuando la coordinadora revisa)
    estado = models.CharField(max_length=15, choices=ESTADOS, default='PENDIENTE', db_index=True) # 💥
    observaciones_coordinacion = models.TextField(blank=True, null=True, help_text="Feedback para el docente en caso de correcciones.")
    fecha_revision = models.DateTimeField(null=True, blank=True)
    revisado_por = models.ForeignKey(Personal, on_delete=models.SET_NULL, null=True, blank=True, related_name='evidencias_revisadas')

    class Meta:
        verbose_name = "Evidencia de Docente"
        verbose_name_plural = "Evidencias de Docentes"
        ordering = ['-fecha_envio']

    def __str__(self):
        return f"Evidencia de {self.docente.apellidos} - {self.estado}"

class HorarioClase(models.Model):
    """ Matriz semanal fija de las horas de clase por aula y docente """
    DIAS_SEMANA = [
        ('LU', 'Lunes'),
        ('MA', 'Martes'),
        ('MI', 'Miércoles'),
        ('JU', 'Jueves'),
        ('VI', 'Viernes'),
    ]

    # 💥 OPTIMIZADO: Ahora es opcional y seguro ante eliminaciones (SET_NULL)
    personal = models.ForeignKey(
        Personal, 
        on_delete=models.SET_NULL, # Si se borra el docente, el bloque se queda en NULL pero NO se elimina el horario
        null=True, 
        blank=True,
        related_name='horarios', 
        limit_choices_to={'cargo': 'DOC'}, 
        verbose_name="Docente"
    )
    aula = models.ForeignKey('Aula', on_delete=models.CASCADE, related_name='horarios')
    curso = models.ForeignKey('Curso', on_delete=models.CASCADE, related_name='horarios')
    periodo = models.ForeignKey('PeriodoLectivo', on_delete=models.CASCADE, related_name='horarios')
    # NUEVO CAMPO DE COLOR
    color = models.CharField(max_length=7, default='#17c1e8', verbose_name="Color de Bloque")
    dia_semana = models.CharField(max_length=2, choices=DIAS_SEMANA, db_index=True) # 💥
    hora_inicio = models.TimeField(db_index=True) # 💥
    hora_fin = models.TimeField(db_index=True) # 💥

    class Meta:
        verbose_name = "Horario de Clase"
        verbose_name_plural = "Horarios de Clases"
        ordering = ['dia_semana', 'hora_inicio']

    def __str__(self):
        # Formateo correcto en Python puro
        hora_str = self.hora_inicio.strftime('%H:%M') if self.hora_inicio else '--:--'
        return f"{self.get_dia_semana_display()} | {hora_str} - {self.curso.nombre} ({self.aula.grado} {self.aula.seccion})"

    def clean(self):
        """ Filtro inteligente de consistencia matemática para evitar cruces de horarios """
        if self.hora_inicio >= self.hora_fin:
            raise ValidationError("La hora de inicio debe ser menor que la hora de fin.")
        
        # 💥 BLINDAJE SENIOR: Solo validamos disponibilidad de agenda si hay un docente asignado
        if self.personal:
            cruces_docente = HorarioClase.objects.filter(
                periodo=self.periodo,
                dia_semana=self.dia_semana,
                personal=self.personal,
                hora_inicio__lt=self.hora_fin,
                hora_fin__gt=self.hora_inicio
            ).exclude(pk=self.pk)
            
            if cruces_docente.exists():
                raise ValidationError(f"Conflicto de disponibilidad: El docente {self.personal} ya está asignado a otra aula en este bloque horario.")

        # La validación de aula física sí se hace siempre (no puede haber dos cursos distintos en la misma aula)
        cruces_aula = HorarioClase.objects.filter(
            periodo=self.periodo,
            dia_semana=self.dia_semana,
            aula=self.aula,
            hora_inicio__lt=self.hora_fin,
            hora_fin__gt=self.hora_inicio
        ).exclude(pk=self.pk)
        
        if cruces_aula.exists():
            raise ValidationError("Conflicto de infraestructura: El aula seleccionada ya está ocupada en este bloque horario.")

class EventoCronograma(models.Model):
    # 💥 LAS OPCIONES DEL CEREBRO DE ALERTAS
    TIPOS_ACADEMICOS = [
        ('NINGUNO', '📌 Evento Regular / Sin alerta'),
        ('TEMA_1', '📘 Tema 1'),
        ('TEMA_2', '📘 Tema 2'),
        ('TEMA_3', '📘 Tema 3'),
        ('TEMA_4', '📘 Tema 4'),
        ('TEMA_5', '📘 Tema 5'),
        ('TEMA_6', '📘 Tema 6'),
        ('CALIDAD', '📝 Examen: Control de Calidad'),
        ('ISO', '🎓 Examen: ISO Ingeniería'),
        ('SIMULACRO', '🏆 Concurso de Aptitud (Simulacro)'),
    ]
    
    """ Agenda dinámica administrada por la Coordinación con rango de fechas y color personalizado """
    titulo = models.CharField(max_length=150, verbose_name="Título del Evento")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Detalles o Instrucciones")
    
    # 💥 NUEVO CAMPO: El puente para las alertas
    tipo_academico = models.CharField(
        max_length=20, 
        choices=TIPOS_ACADEMICOS, 
        default='NINGUNO', 
        verbose_name="Hito Académico",
        db_index=True # Ayuda a que el sistema busque rápido para lanzar alertas
    )
    
    # Rango de fechas
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio", db_index=True) # 💥
    fecha_fin = models.DateField(verbose_name="Fecha de Fin", db_index=True) # 💥
    
    # Color hexadecimal de la etiqueta (con un valor por defecto elegante)
    color = models.CharField(max_length=7, default='#e91e63', verbose_name="Color de Etiqueta")
    
    aula_afectada = models.ForeignKey('Aula', on_delete=models.SET_NULL, null=True, blank=True, help_text="Opcional: Si aplica solo a un salón.")
    
    # Auditoría
    creado_por = models.ForeignKey(Personal, on_delete=models.CASCADE, limit_choices_to={'cargo__in': ['COO', 'DIR']})
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    # 💥 NUEVOS CAMPOS ADAPTATIVOS PARA LA VISTA SEMANAL
    hora_inicio = models.TimeField(null=True, blank=True, verbose_name="Hora de Inicio")
    hora_fin = models.TimeField(null=True, blank=True, verbose_name="Hora de Fin")

    class Meta:
        verbose_name = "Evento de Cronograma"
        verbose_name_plural = "Eventos del Cronograma"
        ordering = ['fecha_inicio', 'hora_inicio', 'fecha_creacion']

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.fecha_inicio > self.fecha_fin:
            raise ValidationError("La fecha de inicio no puede ser posterior a la fecha de fin.")
        if self.hora_inicio and self.hora_fin:
            if self.hora_inicio >= self.hora_fin:
                raise ValidationError("La hora de inicio debe ser menor que la hora de fin.")

    def __str__(self):
        hora_str = self.hora_inicio.strftime('%H:%M') if self.hora_inicio else '--:--'
        return f"{self.titulo} ({self.fecha_inicio.strftime('%d/%m/%Y')} - {self.fecha_fin.strftime('%d/%m/%Y')}, {hora_str})"

class HorarioRecreo(models.Model):
    NIVEL_CHOICES = [
        ('INICIAL', 'Inicial'),
        ('PRIMARIA', 'Primaria'),
        ('SECUNDARIA', 'Secundaria'),
    ]
    nivel = models.CharField(max_length=15, choices=NIVEL_CHOICES, unique=True, verbose_name="Nivel Escolar")
    hora_inicio = models.TimeField(verbose_name="Hora de Inicio")
    hora_fin = models.TimeField(verbose_name="Hora de Fin")
    nombre = models.CharField(max_length=50, default="RECREO", verbose_name="Etiqueta")

    def __str__(self):
        return f"Recreo {self.get_nivel_display()} ({self.hora_inicio.strftime('%I:%M %p')} - {self.hora_fin.strftime('%I:%M %p')})"

    class Meta:
        verbose_name = "Horario de Recreo"
        verbose_name_plural = "Horarios de Recreo"

# ==========================================
# MÓDULO DE INVENTARIO Y LOGÍSTICA
# ==========================================

class CatalogoMaterial(models.Model):
    """ El diccionario global de objetos. SOLO la coordinadora puede crear/editar aquí. """
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Material")
    activo = models.BooleanField(default=True, help_text="Desmarcar si ya no se usa")

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Catálogo de Material"
        verbose_name_plural = "Catálogo de Materiales"
        ordering = ['nombre']


class InventarioAula(models.Model):
    """ El registro específico de un salón en un año determinado. Lo llenan los docentes. """
    periodo = models.ForeignKey(PeriodoLectivo, on_delete=models.CASCADE, related_name='inventarios')
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE, related_name='inventarios')
    material = models.ForeignKey(CatalogoMaterial, on_delete=models.PROTECT, related_name='inventarios_aula')
    
    # Cantidades según el estado
    buen_estado = models.PositiveIntegerField(default=0, verbose_name="Buen Estado")
    regular = models.PositiveIntegerField(default=0, verbose_name="Regular")
    mal_estado = models.PositiveIntegerField(default=0, verbose_name="Mal Estado")
    se_requiere = models.PositiveIntegerField(default=0, verbose_name="Se Requiere (Faltantes)")
    
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    actualizado_por = models.ForeignKey('personal.Personal', on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def cantidad_existente(self):
        """ Calcula automáticamente cuánto material físico hay en el aula """
        return self.buen_estado + self.regular + self.mal_estado

    def __str__(self):
        return f"{self.material.nombre} - {self.aula} ({self.periodo})"

    class Meta:
        verbose_name = "Inventario de Aula"
        verbose_name_plural = "Inventarios de Aulas"
        # REGLA DE ORO: Evita que un profesor registre "Silla" dos veces en el mismo salón y mismo año
        unique_together = ['periodo', 'aula', 'material']
        
class Simulacro(models.Model):
    """
    Controla el evento del examen mensual.
    Ejemplo: Simulacro II - Abril - 6to Grado de Primaria
    """
    periodo = models.ForeignKey(PeriodoLectivo, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100, help_text="Ej: II CONCURSO DE APTITUD ACADÉMICA")
    mes = models.CharField(max_length=50, help_text="Ej: Abril, Mayo")
    
    # Lo vinculamos por Grado y Nivel para que agrupe a todas las secciones
    grado = models.CharField(max_length=50, verbose_name="Grado/Año") 
    nivel = models.CharField(max_length=20, choices=Aula.NIVELES)
    
    fecha_examen = models.DateField()
    
    # 💥 NUEVO CAMPO: Total de preguntas que debe tener este examen en específico
    preguntas_esperadas = models.PositiveIntegerField(
        default=100, 
        help_text="Ej: 40 para Inicial, 100 para Primaria, 120 para Secundaria"
    )
    
    activo = models.BooleanField(default=True, help_text="Si está activo, los profesores pueden enviar preguntas")

    class Meta:
        verbose_name = "Simulacro"
        verbose_name_plural = "Simulacros"

    def __str__(self):
        return f"{self.titulo} - {self.grado} {self.nivel} ({self.mes})"


class PreguntaSimulacro(models.Model):
    """
    Almacena cada pregunta individual enviada por los docentes.
    """
    OPCIONES_CORRECTAS = [
        ('a', 'Opción A'), ('b', 'Opción B'), ('c', 'Opción C'),
        ('d', 'Opción D'), ('e', 'Opción E')
    ]

    simulacro = models.ForeignKey(Simulacro, on_delete=models.CASCADE, related_name='preguntas')
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    docente = models.ForeignKey(
        'personal.Personal', 
        on_delete=models.CASCADE, 
        related_name='preguntas_simulacro'
    )

    enunciado = models.TextField(help_text="Texto principal de la pregunta")
    
    # 💥 El campo estrella: Permite subir imágenes de gráficos o fórmulas complejas
    imagen = models.ImageField(upload_to='simulacros/imagenes/', blank=True, null=True, help_text="Opcional. Sube la imagen del gráfico o fórmula.")

    # Las 5 alternativas (A y B suelen ser obligatorias siempre)
    opcion_a = models.CharField(max_length=255)
    opcion_b = models.CharField(max_length=255)
    
    # 💥 Ahora C, D y E son opcionales
    opcion_c = models.CharField(max_length=255, blank=True, null=True)
    opcion_d = models.CharField(max_length=255, blank=True, null=True)
    opcion_e = models.CharField(max_length=255, blank=True, null=True, default="N.A.")

    respuesta_correcta = models.CharField(max_length=1, choices=OPCIONES_CORRECTAS)

    class Meta:
        verbose_name = "Pregunta de Simulacro"
        verbose_name_plural = "Preguntas de Simulacro"
        ordering = ['curso__nombre', 'id'] # Agrupará las preguntas por curso automáticamente

    def __str__(self):
        return f"Pregunta de {self.curso.nombre} - {self.simulacro}"

class EntregaSimulacro(models.Model):
    """ Almacena el estado de finalización del envío de preguntas por curso """
    simulacro = models.ForeignKey(Simulacro, on_delete=models.CASCADE, related_name='entregas_control')
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    docente = models.ForeignKey('personal.Personal', on_delete=models.CASCADE)
    finalizado = models.BooleanField(default=False, verbose_name="¿Envío Terminado?")
    fecha_entrega = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['simulacro', 'curso', 'docente']

    def __str__(self):
        return f"{self.curso.nombre} - {self.docente.apellidos} ({'Finalizado' if self.finalizado else 'Pendiente'})"
    

class Institucion(models.Model):
    nombre = models.CharField(max_length=100, default="Consorcio Educativo Ingeniería")
    sede = models.CharField(max_length=100, default="Sede Principal")
    direccion = models.CharField(max_length=200, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True, help_text="Número para WhatsApp (+51...)")
    correo = models.EmailField(blank=True, null=True)
    
    # Datos Oficiales
    codigo_modular = models.CharField(max_length=20, blank=True, null=True, verbose_name="Código Modular")
    ruc = models.CharField(max_length=11, blank=True, null=True, verbose_name="RUC")
    director = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nombre del Director(a)")
    
    # Identidad Visual
    logo = models.ImageField(upload_to='institucion/', blank=True, null=True)

    def save(self, *args, **kwargs):
        # Patrón Singleton: Asegura que siempre se guarde en la fila 1
        self.pk = 1 
        super(Institucion, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass # Evita que alguien borre la configuración por error

    class Meta:
        verbose_name = "Institución"
        verbose_name_plural = "Configuración de la Institución"

    def __str__(self):
        return f"{self.nombre} - {self.sede}"

class CierreRegistroBimestral(models.Model):
    """ Actúa como un candado de seguridad por cada curso y bimestre """
    asignacion = models.ForeignKey(AsignacionAcademica, on_delete=models.CASCADE, related_name='cierres')
    bimestre = models.CharField(max_length=5, choices=PeriodoLectivo.BIMESTRES)
    
    cerrado = models.BooleanField(default=False, verbose_name="¿Registro Cerrado?")
    fecha_cierre = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Cierre de Registro"
        verbose_name_plural = "Cierres de Registros"
        # Un profesor solo puede cerrar un bimestre de un curso una sola vez
        unique_together = ['asignacion', 'bimestre']

    def __str__(self):
        estado = "CERRADO" if self.cerrado else "ABIERTO"
        return f"{self.asignacion.curso.nombre} - Bimestre {self.bimestre} ({estado})"