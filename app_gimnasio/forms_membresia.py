from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from .models import Miembro, TipoMembresia, Membresia, Pago, MetodoPago, Banco

class MembresiaForm(forms.ModelForm):
    """Formulario para crear y editar membresías."""
    
    # Campo para seleccionar el miembro con un widget mejorado
    miembro = forms.ModelChoiceField(
        queryset=Miembro.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Miembro"
    )
    
    # Campo para seleccionar el tipo de membresía
    tipo_membresia = forms.ModelChoiceField(
        queryset=TipoMembresia.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Tipo de Membresía"
    )
    
    # Campos de fecha con widget de tipo date
    fecha_inicio = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        initial=timezone.now().date(),
        label="Fecha de Inicio"
    )
    
    fecha_vencimiento = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        label="Fecha de Vencimiento"
    )
    
    # Campo para el precio con un valor inicial
    precio = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        label="Precio"
    )
    
    # Campo para indicar si la membresía está activa
    activa = forms.BooleanField(
        required=False,
        initial=True,
        label="Activa"
    )
    
    # Campos para el pago inicial (opcional)
    registrar_pago = forms.BooleanField(
        required=False,
        initial=True,
        label="Registrar Pago Inicial"
    )
    
    monto_pago = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        label="Monto del Pago"
    )
    
    metodo_pago = forms.ModelChoiceField(
        queryset=MetodoPago.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Método de Pago"
    )
    
    banco = forms.ModelChoiceField(
        queryset=Banco.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Banco"
    )
    
    referencia = forms.CharField(
        max_length=50,
        required=False,
        label="Referencia"
    )
    
    class Meta:
        model = Membresia
        fields = [
            'miembro', 'tipo_membresia', 'fecha_inicio', 'fecha_vencimiento',
            'precio', 'activa', 'notas'
        ]
        widgets = {
            'notas': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si es una edición, no permitir cambiar el miembro
        if self.instance and self.instance.pk:
            self.fields['miembro'].disabled = True
        
        # Inicializar el precio basado en el tipo de membresía seleccionado
        if 'tipo_membresia' in self.data:
            try:
                tipo_id = int(self.data.get('tipo_membresia'))
                tipo = TipoMembresia.objects.get(pk=tipo_id)
                self.fields['precio'].initial = tipo.precio_estandar
                
                # Calcular fecha de vencimiento basada en la duración del tipo
                if 'fecha_inicio' in self.data and self.data.get('fecha_inicio'):
                    try:
                        fecha_inicio = forms.DateField().clean(self.data.get('fecha_inicio'))
                        self.fields['fecha_vencimiento'].initial = fecha_inicio + timedelta(days=tipo.duracion_dias)
                    except (ValueError, ValidationError):
                        pass
            except (ValueError, TipoMembresia.DoesNotExist):
                pass
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_vencimiento = cleaned_data.get('fecha_vencimiento')
        tipo_membresia = cleaned_data.get('tipo_membresia')
        registrar_pago = cleaned_data.get('registrar_pago')
        monto_pago = cleaned_data.get('monto_pago')
        metodo_pago = cleaned_data.get('metodo_pago')
        
        # Validar fechas
        if fecha_inicio and fecha_vencimiento and fecha_inicio >= fecha_vencimiento:
            self.add_error('fecha_vencimiento', 'La fecha de vencimiento debe ser posterior a la fecha de inicio.')
        
        # Si no se proporciona fecha de vencimiento, calcularla basada en el tipo
        if fecha_inicio and tipo_membresia and not fecha_vencimiento:
            cleaned_data['fecha_vencimiento'] = fecha_inicio + timedelta(days=tipo_membresia.duracion_dias)
        
        # Validar campos de pago
        if registrar_pago:
            if not monto_pago:
                self.add_error('monto_pago', 'Debe especificar el monto del pago.')
            if not metodo_pago:
                self.add_error('metodo_pago', 'Debe seleccionar un método de pago.')
        
        return cleaned_data
    
    def save(self, commit=True):
        membresia = super().save(commit=False)
        
        # Asignar el precio del formulario al campo precio_pagado del modelo
        membresia.precio_pagado = self.cleaned_data.get('precio')
        
        # Asegurarse de que la fecha de vencimiento está establecida
        if not membresia.fecha_vencimiento and membresia.fecha_inicio and membresia.tipo_membresia:
            membresia.fecha_vencimiento = membresia.fecha_inicio + timedelta(days=membresia.tipo_membresia.duracion_dias)
        
        if commit:
            membresia.save()
            
            # Crear el pago inicial si se ha seleccionado
            if self.cleaned_data.get('registrar_pago'):
                Pago.objects.create(
                    membresia=membresia,
                    miembro=membresia.miembro,
                    monto=self.cleaned_data.get('monto_pago'),
                    metodo_pago=self.cleaned_data.get('metodo_pago'),
                    banco=self.cleaned_data.get('banco'),
                    referencia_pago=self.cleaned_data.get('referencia')
                    # fecha_pago se asigna automáticamente por auto_now_add=True
                )
        
        return membresia
