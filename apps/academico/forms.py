from django import forms
from .models import AsignacionAcademica, Curso, Estudiante, Aula, EventoCronograma, EvidenciaDocente, HorarioClase, Institucion, MaterialInstitucional, PeriodoLectivo, PreguntaSimulacro, Simulacro
from apps.personal.models import Personal

class EstudianteForm(forms.ModelForm):
    class Meta:
        model = Estudiante
        fields = ['nombres', 'apellidos', 'dni', 'telefono_apoderado', 'direccion', 'estado']
        # Aquí le agregamos las clases de Bootstrap/Material Dashboard a los inputs
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Juan Pérez'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Pérez Gómez'}),
            'dni': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '8 dígitos', 'maxlength': '8'}),
            'telefono_apoderado': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
        }

class AulaForm(forms.ModelForm):
    class Meta:
        model = Aula
        # 💥 AGREGAMOS 'google_sheet_id' A LA LISTA DE CAMPOS
        fields = ['grado', 'nivel', 'seccion', 'denominacion', 'tutor', 'google_sheet_id'] 
        widgets = {
            'nivel': forms.Select(attrs={'class': 'form-control'}),
            'grado': forms.Select(attrs={'class': 'form-control'}),
            'seccion': forms.Select(attrs={'class': 'form-control'}),
            'denominacion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional'}),
            'tutor': forms.Select(attrs={'class': 'form-control'}),
            # 💥 AGREGAMOS EL WIDGET PARA QUE TENGA EL DISEÑO CORRECTO
            'google_sheet_id': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej: 1MQlfPcVd3b_jcGjsLcYoRzXVn30ZhUvenDqNptU-loM'
            }),
        }

    def __init__(self, *args, **kwargs):
        super(AulaForm, self).__init__(*args, **kwargs)
        
        # Filtramos para que solo muestre a los Docentes Activos y Fijos
        self.fields['tutor'].queryset = Personal.objects.filter(
            cargo='DOC', 
            estado='Activo', 
            tipo_contrato='Fijo'
        ).order_by('apellidos', 'nombres')
        
        # Le ponemos el texto por defecto para que no obligue a elegir uno
        self.fields['tutor'].empty_label = "-- Sin tutor asignado --"

class PeriodoLectivoForm(forms.ModelForm):
    class Meta:
        model = PeriodoLectivo
        # 1. Cambiamos 'nombre' por 'anio'
        fields = ['anio', 'activo', 'bimestre_actual'] 
        widgets = {
            # 2. Usamos NumberInput para que el celular abra el teclado numérico
            'anio': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 2026'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'bimestre_actual': forms.Select(attrs={'class': 'form-control border-bottom border-2 px-3 py-1'}),
        }

class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        # 💥 AGREGAMOS 'area' A LA LISTA
        fields = ['nombre', 'area', 'descripcion', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'area': forms.Select(attrs={'class': 'form-control'}), # Widget para el nuevo select
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class AsignacionAcademicaForm(forms.ModelForm):
    class Meta:
        model = AsignacionAcademica
        fields = ['personal', 'curso', 'aula', 'periodo']
        widgets = {
            'personal': forms.Select(attrs={'class': 'form-control'}),
            'curso': forms.Select(attrs={'class': 'form-control'}),
            'aula': forms.Select(attrs={'class': 'form-control'}),
            'periodo': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtramos para que solo salgan los docentes activos (fijos o por horas)
        self.fields['personal'].queryset = Personal.objects.filter(cargo='DOC', estado='Activo')
        self.fields['personal'].empty_label = "-- Seleccione un Docente --"
        
        # Filtramos para que aparezca por defecto solo el periodo activo
        self.fields['periodo'].queryset = PeriodoLectivo.objects.filter(activo=True)
        self.fields['curso'].empty_label = "-- Seleccione un Curso --"
        self.fields['aula'].empty_label = "-- Seleccione un Aula --"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # FILTROS INTELIGENTES: Solo mostramos opciones válidas/activas
        self.fields['personal'].queryset = Personal.objects.filter(cargo='DOC', estado='Activo')
        # Si usaste el switch booleano en Cursos (activo=True), usa esto:
        self.fields['curso'].queryset = Curso.objects.filter(activo=True) 
        # Si dejaste el estado de cursos como texto ('Activo'), usa esto en su lugar:
        # self.fields['curso'].queryset = Curso.objects.filter(estado='Activo')
        
        # Opcional: Que por defecto aparezca seleccionado el Periodo actual
        periodo_actual = PeriodoLectivo.objects.filter(activo=True).first()
        if periodo_actual:
            self.fields['periodo'].initial = periodo_actual

class MaterialInstitucionalForm(forms.ModelForm):
    class Meta:
        model = MaterialInstitucional
        fields = ['titulo', 'descripcion', 'categoria', 'archivo']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Formato de Examen Bimestral'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Indicaciones opcionales...'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'archivo': forms.FileInput(attrs={'class': 'form-control', 'required': True}),
        }

class EvidenciaDocenteForm(forms.ModelForm):
    class Meta:
        model = EvidenciaDocente
        fields = ['titulo', 'descripcion', 'archivo_evidencia']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Evidencia Mural - Mayo'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Comentarios para coordinación...'}),
            'archivo_evidencia': forms.FileInput(attrs={'class': 'form-control', 'required': True}),
        }

class HorarioClaseForm(forms.ModelForm):
    class Meta:
        model = HorarioClase
        fields = ['personal', 'aula', 'curso', 'periodo', 'dia_semana', 'hora_inicio', 'hora_fin', 'color']
        widgets = {
            'personal': forms.Select(attrs={'class': 'form-control'}),
            'aula': forms.Select(attrs={'class': 'form-control'}),
            'curso': forms.Select(attrs={'class': 'form-control'}),
            'periodo': forms.Select(attrs={'class': 'form-control'}),
            'dia_semana': forms.Select(attrs={'class': 'form-control'}),
            'hora_inicio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'hora_fin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'color': forms.TextInput(attrs={'class': 'form-control form-control-color w-100', 'type': 'color', 'style': 'height: 40px; border-radius: 0.375rem;'}),
        }

class EventoCronogramaForm(forms.ModelForm):
    class Meta:
        model = EventoCronograma
        fields = ['titulo', 'descripcion', 'fecha_inicio', 'fecha_fin', 'color', 'aula_afectada', 'tipo_academico']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Entrega de Registros', 'required': True}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Detalles opcionales...'}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': True}),
            'fecha_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': True}),
            'color': forms.TextInput(attrs={'class': 'form-control form-control-color w-100', 'type': 'color', 'style': 'height: 40px; border-radius: 0.375rem;'}),
            'aula_afectada': forms.Select(attrs={'class': 'form-control'}),
            'tipo_academico': forms.Select(attrs={'class': 'form-control border-bottom border-2 px-3 py-1'}),
        }

class SimulacroForm(forms.ModelForm):
    class Meta:
        model = Simulacro
        fields = ['titulo', 'mes', 'grado', 'nivel', 'fecha_examen', 'preguntas_esperadas', 'activo']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: II CONCURSO DE APTITUD ACADÉMICA'}),
            'mes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Abril'}),
            'grado': forms.Select(choices=Aula.GRADOS, attrs={'class': 'form-control'}),
            'nivel': forms.Select(choices=Aula.NIVELES, attrs={'class': 'form-control'}),
            'fecha_examen': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'preguntas_esperadas': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 100'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PreguntaSimulacroForm(forms.ModelForm):
    class Meta:
        model = PreguntaSimulacro
        # No incluimos 'simulacro' ni 'docente' porque los asignaremos automáticamente en la vista
        fields = ['curso', 'enunciado', 'imagen', 'opcion_a', 'opcion_b', 'opcion_c', 'opcion_d', 'opcion_e', 'respuesta_correcta']
        widgets = {
            'curso': forms.Select(attrs={'class': 'form-control border-bottom border-2 px-3'}),
            'enunciado': forms.Textarea(attrs={'class': 'form-control border border-2 p-2', 'rows': 3, 'placeholder': 'Escriba aquí el enunciado de la pregunta...'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'opcion_a': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Alternativa A'}),
            'opcion_b': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Alternativa B'}),
            'opcion_c': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Alternativa C'}),
            'opcion_d': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Alternativa D'}),
            'opcion_e': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Alternativa E (Por defecto N.A.)'}),
            'respuesta_correcta': forms.Select(attrs={'class': 'form-control border-bottom border-2 px-3'}),
        }
    
class InstitucionForm(forms.ModelForm):
    class Meta:
        model = Institucion
        # Eliminamos 'director' de la lista de campos
        exclude = ['director'] 
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control px-3', 'placeholder': 'Nombre de la institución'}),
            'sede': forms.TextInput(attrs={'class': 'form-control px-3', 'placeholder': 'Ej. Torre Blanca'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control px-3', 'placeholder': 'Dirección completa'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control px-3', 'placeholder': '+51 999 999 999'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control px-3', 'placeholder': 'correo@colegio.edu.pe'}),
            'codigo_modular': forms.TextInput(attrs={'class': 'form-control px-3', 'placeholder': 'Ej. 1234567'}),
            'ruc': forms.TextInput(attrs={'class': 'form-control px-3', 'placeholder': 'RUC de 11 dígitos'}),
            # El input file lo ocultamos con 'd-none' para usar nuestro propio botón de diseño
            'logo': forms.FileInput(attrs={'class': 'd-none', 'accept': 'image/*', 'id': 'logoInput', 'onchange': 'previewImage(event)'}),
        }