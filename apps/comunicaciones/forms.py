from django import forms
from .models import Comunicado

class ComunicadoForm(forms.ModelForm):
    class Meta:
        model = Comunicado
        fields = ['titulo', 'mensaje', 'importancia', 'audiencia', 'fecha_expiracion', 'archivo_adjunto', 'activo']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control border bg-white px-2', 'placeholder': 'Ej: Reunión de Padres'}),
            'mensaje': forms.Textarea(attrs={'class': 'form-control border bg-white px-2', 'rows': 4, 'placeholder': 'Redacte el comunicado aquí...'}),
            'importancia': forms.Select(attrs={'class': 'form-control border bg-white px-2'}),
            'audiencia': forms.Select(attrs={'class': 'form-control border bg-white px-2'}),
            'fecha_expiracion': forms.DateTimeInput(attrs={'class': 'form-control border bg-white px-2', 'type': 'datetime-local'}),
            'archivo_adjunto': forms.FileInput(attrs={'class': 'form-control border bg-white px-2'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_activo'}),
        }