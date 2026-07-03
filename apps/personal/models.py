from django.db import models
from django.contrib.auth.models import User

class Personal(models.Model):
    CARGOS = [
        ('DIR', 'Director(a)'),
        ('COO', 'Coordinador(a)'),
        ('DOC', 'Docente'),
        ('SEC', 'Secretaria(o)'),
        ('ASI', 'Asistente'),
        ('AUX', 'Auxiliar'),
        ('LIM', 'Personal de Limpieza'),
    ]

    ESTADOS = [
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
    ]
    
    TIPOS_CONTRATO = [
        ('Fijo', 'Fijo (Tiempo Completo)'),
        ('Por Horas', 'Por Horas (Secundaria/Talleres)'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='perfil_personal',
        verbose_name="Cuenta de Usuario"
    )

    # Datos Personales
    dni = models.CharField(max_length=8, unique=True, verbose_name="DNI")
    nombres = models.CharField(max_length=100)
    # 💥 Optimizado: Porque ordenas las listas usando este campo (ordering = ['cargo', 'apellidos',...])
    apellidos = models.CharField(max_length=100, db_index=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    correo = models.EmailField(blank=True, null=True)
    
    # Datos Laborales
    # 💥 Optimizado: Para buscar rapidísimo quién es 'DOC' (Docente) o 'COO' (Coordinador)
    cargo = models.CharField(max_length=3, choices=CARGOS, default='DOC', verbose_name="Cargo", db_index=True)
    tipo_contrato = models.CharField(max_length=20, choices=TIPOS_CONTRATO, verbose_name="Tipo de Contrato")
    
    # 💥 Optimizado: Todo el sistema filtra por personal 'Activo'
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Activo', db_index=True)
    fecha_ingreso = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.apellidos}, {self.nombres} - {self.get_cargo_display()}"
    
    class Meta:
        verbose_name = "Personal"
        verbose_name_plural = "Personal del Colegio"
        ordering = ['cargo', 'apellidos', 'nombres']