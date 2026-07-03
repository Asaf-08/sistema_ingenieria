from django import forms

from apps.personal.models import Personal

class PersonalForm(forms.ModelForm):
    class Meta:
        model = Personal
        fields = ['dni', 'nombres', 'apellidos', 'cargo', 'tipo_contrato', 'fecha_ingreso', 'telefono', 'correo']
        widgets = {
            'dni': forms.TextInput(attrs={'class': 'form-control'}),
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'cargo': forms.Select(attrs={'class': 'form-control'}),
            'tipo_contrato': forms.Select(attrs={'class': 'form-control'}),
            'fecha_ingreso': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class EditarPerfilForm(forms.ModelForm):
    class Meta:
        model = Personal
        fields = ['telefono', 'correo']
        widgets = {
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'tel'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'}),
        }
        labels = {
            'telefono': 'Teléfono / Celular',
            'correo': 'Correo Electrónico de Contacto',
        }