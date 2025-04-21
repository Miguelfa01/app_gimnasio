from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from .models import Miembro, Objetivo, TipoMembresia, Membresia, Pago, MetodoPago, Banco

class MiembroForm(forms.ModelForm):
    """Formulario para crear y editar miembros."""
    
    # Campo para seleccionar múltiples objetivos con un widget mejorado
    objetivos = forms.ModelMultipleChoiceField(
        queryset=Objetivo.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Objetivos"
    )
    
    # Campos de fecha con widget de tipo date
    fecha_nacimiento = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        label="Fecha de Nacimiento"
    )
    
    class Meta:
        model = Miembro
        fields = [
            'cedula', 'nombre', 'apellido', 'fecha_nacimiento', 
            'telefono', 'correo_electronico', 'direccion', 
            'foto', 'condicion_medica', 
            'contacto_emergencia_nombre', 'contacto_emergencia_parentesco', 'contacto_emergencia_telefono',
            'id_huella', 'notas', 'objetivos'
        ]
        widgets = {
            'direccion': forms.Textarea(attrs={'rows': 3}),
            'condicion_medica': forms.Textarea(attrs={'rows': 3}),
            'notas': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean_cedula(self):
        """Validar que la cédula sea única."""
        cedula = self.cleaned_data.get('cedula')
        
        # Si estamos editando un miembro existente, excluimos su propio ID
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            miembro_exists = Miembro.objects.filter(cedula=cedula).exclude(pk=instance.pk).exists()
        else:
            miembro_exists = Miembro.objects.filter(cedula=cedula).exists()
        
        if miembro_exists:
            raise ValidationError("Ya existe un miembro con esta cédula.")
        
        return cedula
    
    def clean_correo_electronico(self):
        """Validar que el correo electrónico sea único si se proporciona."""
        email = self.cleaned_data.get('correo_electronico')
        
        if not email:
            return email
            
        # Si estamos editando un miembro existente, excluimos su propio ID
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            email_exists = Miembro.objects.filter(correo_electronico=email).exclude(pk=instance.pk).exists()
        else:
            email_exists = Miembro.objects.filter(correo_electronico=email).exists()
        
        if email_exists:
            raise ValidationError("Ya existe un miembro con este correo electrónico.")
        
        return email

class ObjetivoForm(forms.ModelForm):
    class Meta:
        model = Objetivo
        fields = ['nombre', 'descripcion']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }
