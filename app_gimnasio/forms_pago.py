from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Sum  # <-- Agrega este import
from .models import Pago, Miembro, Membresia, MetodoPago, Banco

class PagoForm(forms.ModelForm):
    """Formulario para crear y editar pagos."""
    
    # Campo para el textbox de autocompletado de miembro
    miembro_autocomplete = forms.CharField(
        label="Miembro",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'off',
            'placeholder': 'Buscar miembro por nombre...'
        })
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
            'membresia', 'monto', 'metodo_pago', 
            'banco', 'referencia_pago', 'notas'
        ]
        widgets = {
            'notas': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        miembro_id = None
        miembro_nombre = None
        # Buscar miembro en initial o data
        if 'initial' in kwargs and kwargs['initial'].get('miembro_autocomplete'):
            miembro_nombre = kwargs['initial']['miembro_autocomplete']
        elif 'data' in kwargs and kwargs['data'].get('miembro_autocomplete'):
            miembro_nombre = kwargs['data']['miembro_autocomplete']

        if miembro_nombre:
            try:
                miembro_id = int(miembro_nombre)
            except (ValueError, TypeError):
                miembro_id = None
        super().__init__(*args, **kwargs)
        
        # Actualizar queryset de membresía según el miembro seleccionado
        if miembro_id:
            try:
                miembro = Miembro.objects.get(pk=miembro_id)
                self.fields['membresia'].queryset = Membresia.objects.filter(miembro=miembro, activa=True)
            except Miembro.DoesNotExist:
                self.fields['membresia'].queryset = Membresia.objects.none()
        elif miembro_nombre:
            miembros = Miembro.objects.filter(nombre__icontains=miembro_nombre)
            if miembros.exists():
                self.fields['membresia'].queryset = Membresia.objects.filter(miembro=miembros.first(), activa=True)
            else:
                self.fields['membresia'].queryset = Membresia.objects.none()
        else:
            self.fields['membresia'].queryset = Membresia.objects.none()
        
        # Si es una edición, no permitir cambiar el miembro ni la membresía
        if self.instance and self.instance.pk:
            self.fields['membresia'].disabled = True
            
            # Establecer el queryset de membresías para el miembro seleccionado
            if self.instance.miembro:
                self.fields['membresia'].queryset = Membresia.objects.filter(miembro=self.instance.miembro)
        
        # Si hay datos en el formulario, actualizar el queryset de membresías
        elif 'membresia' in self.data:
            try:
                membresia_id = int(self.data.get('membresia'))
                membresia = Membresia.objects.get(pk=membresia_id)
                # Calcular el saldo pendiente
                saldo_pendiente = membresia.precio_pagado
                pagos_realizados = Pago.objects.filter(membresia=membresia).aggregate(total=Sum('monto'))
                if pagos_realizados['total']:
                    saldo_pendiente -= pagos_realizados['total']
                if saldo_pendiente > 0:
                    # Limita el saldo pendiente a dos decimales para mostrar en el campo monto
                    self.fields['monto'].initial = round(saldo_pendiente, 2)
            except (ValueError, Membresia.DoesNotExist):
                pass
        elif self.initial.get('membresia'):
            membresia = self.initial.get('membresia')
            # Si membresia es un ID (int), obtener la instancia
            if isinstance(membresia, int):
                try:
                    membresia = Membresia.objects.get(pk=membresia)
                except Membresia.DoesNotExist:
                    membresia = None
            if membresia:
                # Calcular el saldo pendiente
                saldo_pendiente = membresia.precio_pagado
                pagos_realizados = Pago.objects.filter(membresia=membresia).aggregate(total=Sum('monto'))
                if pagos_realizados['total']:
                    saldo_pendiente -= pagos_realizados['total']
                if saldo_pendiente > 0:
                    # Limita el saldo pendiente a dos decimales para mostrar en el campo monto
                    self.fields['monto'].initial = round(saldo_pendiente, 2)
    
    def clean(self):
        cleaned_data = super().clean()
        miembro_nombre = cleaned_data.get('miembro_autocomplete')
        membresia = cleaned_data.get('membresia')
        monto = cleaned_data.get('monto')
        metodo_pago = cleaned_data.get('metodo_pago')
        banco = cleaned_data.get('banco')
        
        try:
            miembro_id = int(miembro_nombre)
        except ValueError:
            miembro_id = None
        
        if miembro_id:
            try:
                miembro = Miembro.objects.get(pk=miembro_id)
            except Miembro.DoesNotExist:
                self.add_error('miembro_autocomplete', 'Miembro no encontrado.')
        elif miembro_nombre:
            miembros = Miembro.objects.filter(nombre__icontains=miembro_nombre)
            if miembros.exists():
                miembro = miembros.first()
            else:
                self.add_error('miembro_autocomplete', 'Miembro no encontrado.')
        else:
            self.add_error('miembro_autocomplete', 'Debe proporcionar un miembro.')
        
        if 'miembro' in locals() and membresia and membresia.miembro != miembro:
            self.add_error('membresia', 'La membresía seleccionada no pertenece al miembro seleccionado.')
        
        # Validar que se proporcione un banco si el método de pago lo requiere
        if metodo_pago and metodo_pago.requiere_banco and not banco:
            self.add_error('banco', f'El método de pago {metodo_pago.nombre} requiere seleccionar un banco.')
        
        return cleaned_data
