from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Pago, Miembro, Membresia, MetodoPago, Banco

class PagoForm(forms.ModelForm):
    """Formulario para crear y editar pagos."""
    
    # Campo para seleccionar el miembro con un widget mejorado
    miembro = forms.ModelChoiceField(
        queryset=Miembro.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Miembro"
    )
    
    # Campo para seleccionar la membresía
    membresia = forms.ModelChoiceField(
        queryset=Membresia.objects.none(),  # Se actualizará dinámicamente según el miembro seleccionado
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Membresía Asociada"
    )
    
    # Campo para el monto con un valor inicial
    monto = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        label="Monto del Pago"
    )
    
    # Campo para seleccionar el método de pago
    metodo_pago = forms.ModelChoiceField(
        queryset=MetodoPago.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Método de Pago"
    )
    
    # Campo para seleccionar el banco (opcional)
    banco = forms.ModelChoiceField(
        queryset=Banco.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Banco"
    )
    
    # Campo para la referencia de pago
    referencia_pago = forms.CharField(
        max_length=100,
        required=False,
        label="Referencia/Nº Transacción"
    )
    
    class Meta:
        model = Pago
        fields = [
            'miembro', 'membresia', 'monto', 'metodo_pago', 
            'banco', 'referencia_pago', 'notas'
        ]
        widgets = {
            'notas': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si es una edición, no permitir cambiar el miembro ni la membresía
        if self.instance and self.instance.pk:
            self.fields['miembro'].disabled = True
            self.fields['membresia'].disabled = True
            
            # Establecer el queryset de membresías para el miembro seleccionado
            if self.instance.miembro:
                self.fields['membresia'].queryset = Membresia.objects.filter(miembro=self.instance.miembro)
        
        # Si hay datos en el formulario, actualizar el queryset de membresías
        elif 'miembro' in self.data:
            try:
                miembro_id = int(self.data.get('miembro'))
                self.fields['membresia'].queryset = Membresia.objects.filter(miembro_id=miembro_id)
            except (ValueError, TypeError):
                pass
        # Si hay un miembro preseleccionado en el initial
        elif self.initial.get('miembro'):
            self.fields['membresia'].queryset = Membresia.objects.filter(miembro=self.initial.get('miembro'))
        
        # Si hay una membresía preseleccionada, establecer el monto inicial
        if 'membresia' in self.data:
            try:
                membresia_id = int(self.data.get('membresia'))
                membresia = Membresia.objects.get(pk=membresia_id)
                # Calcular el saldo pendiente
                saldo_pendiente = membresia.precio_pagado
                pagos_realizados = Pago.objects.filter(membresia=membresia).aggregate(total=forms.models.Sum('monto'))
                if pagos_realizados['total']:
                    saldo_pendiente -= pagos_realizados['total']
                if saldo_pendiente > 0:
                    self.fields['monto'].initial = saldo_pendiente
            except (ValueError, Membresia.DoesNotExist):
                pass
        elif self.initial.get('membresia'):
            membresia = self.initial.get('membresia')
            # Calcular el saldo pendiente
            saldo_pendiente = membresia.precio_pagado
            pagos_realizados = Pago.objects.filter(membresia=membresia).aggregate(total=forms.models.Sum('monto'))
            if pagos_realizados['total']:
                saldo_pendiente -= pagos_realizados['total']
            if saldo_pendiente > 0:
                self.fields['monto'].initial = saldo_pendiente
    
    def clean(self):
        cleaned_data = super().clean()
        miembro = cleaned_data.get('miembro')
        membresia = cleaned_data.get('membresia')
        monto = cleaned_data.get('monto')
        metodo_pago = cleaned_data.get('metodo_pago')
        banco = cleaned_data.get('banco')
        
        # Validar que la membresía pertenezca al miembro
        if miembro and membresia and membresia.miembro != miembro:
            self.add_error('membresia', 'La membresía seleccionada no pertenece al miembro seleccionado.')
        
        # Validar que se proporcione un banco si el método de pago lo requiere
        if metodo_pago and metodo_pago.requiere_banco and not banco:
            self.add_error('banco', f'El método de pago {metodo_pago.nombre} requiere seleccionar un banco.')
        
        return cleaned_data
