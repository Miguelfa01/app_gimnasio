from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Objetivo(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Objetivo")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Objetivo"
        verbose_name_plural = "Objetivos"


class MetodoPago(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Método de Pago")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    requiere_banco = models.BooleanField(default=False, verbose_name="¿Requiere Banco?")
    activo = models.BooleanField(default=True, verbose_name="¿Está Activo?")
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Método de Pago"
        verbose_name_plural = "Métodos de Pago"


class Banco(models.Model):
    nombre = models.CharField(max_length=150, unique=True, verbose_name="Nombre del Banco")
    codigo_swift = models.CharField(max_length=11, blank=True, null=True, unique=True, verbose_name="Código SWIFT/BIC")
    activo = models.BooleanField(default=True, verbose_name="¿Está Activo?")
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Banco"
        verbose_name_plural = "Bancos"


class Entrenador(models.Model):
    cedula = models.CharField(max_length=20, unique=True, verbose_name="Cédula")
    nombre = models.CharField(max_length=100, verbose_name="Nombre(s)")
    apellido = models.CharField(max_length=100, verbose_name="Apellido(s)")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    correo_electronico = models.EmailField(blank=True, null=True, verbose_name="Correo Electrónico")
    especialidad = models.CharField(max_length=150, blank=True, null=True, verbose_name="Especialidad")
    fecha_contratacion = models.DateField(blank=True, null=True, verbose_name="Fecha de Contratación")
    activo = models.BooleanField(default=True, verbose_name="¿Está Activo?")
    
    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"
    
    class Meta:
        verbose_name = "Entrenador"
        verbose_name_plural = "Entrenadores"


class TipoMembresia(models.Model):
    nombre = models.CharField(max_length=150, unique=True, verbose_name="Nombre del Plan")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    duracion_dias = models.PositiveIntegerField(verbose_name="Duración Estándar (días)")
    precio_estandar = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Estándar")
    permite_acceso_clases = models.BooleanField(default=True, verbose_name="¿Permite Acceso a Clases?")
    activo = models.BooleanField(default=True, verbose_name="¿Plan Activo?")
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Tipo de Membresía"
        verbose_name_plural = "Tipos de Membresía"


class Miembro(models.Model):
    cedula = models.CharField(max_length=20, unique=True, verbose_name="Cédula")
    nombre = models.CharField(max_length=100, verbose_name="Nombre(s)")
    apellido = models.CharField(max_length=100, verbose_name="Apellido(s)")
    fecha_nacimiento = models.DateField(blank=True, null=True, verbose_name="Fecha de Nacimiento")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    correo_electronico = models.EmailField(blank=True, null=True, verbose_name="Correo Electrónico")
    direccion = models.TextField(blank=True, null=True, verbose_name="Dirección")
    fecha_registro = models.DateField(auto_now_add=True, verbose_name="Fecha de Registro")
    id_huella = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="ID Huella Dactilar")
    foto = models.ImageField(upload_to='fotos_miembros/', blank=True, null=True, verbose_name="Foto")
    condicion_medica = models.TextField(blank=True, null=True, verbose_name="Condiciones Médicas")
    contacto_emergencia_nombre = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nombre Contacto Emergencia")
    contacto_emergencia_parentesco = models.CharField(max_length=50, blank=True, null=True, verbose_name="Parentesco Contacto Emergencia")
    contacto_emergencia_telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono Contacto Emergencia")
    notas = models.TextField(blank=True, null=True, verbose_name="Notas Adicionales")
    objetivos = models.ManyToManyField(Objetivo, blank=True, verbose_name="Objetivos")
    
    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"
    
    def tiene_membresia_activa(self):
        return self.membresia_set.filter(activa=True).exists()
    
    class Meta:
        verbose_name = "Miembro"
        verbose_name_plural = "Miembros"


class Membresia(models.Model):
    ESTADO_PAGO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Parcial', 'Pagado Parcialmente'),
        ('Pagado', 'Pagado Totalmente'),
    ]
    
    miembro = models.ForeignKey(Miembro, on_delete=models.CASCADE, verbose_name="Miembro")
    tipo_membresia = models.ForeignKey(TipoMembresia, on_delete=models.PROTECT, verbose_name="Tipo de Membresía")
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    fecha_vencimiento = models.DateField(verbose_name="Fecha de Vencimiento")
    precio_pagado = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Acordado/Pagado")
    fecha_compra = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Compra/Registro")
    activa = models.BooleanField(default=True, verbose_name="¿Membresía Activa?")
    renovada = models.BooleanField(default=False, verbose_name="¿Renovada?")
    estado_pago = models.CharField(max_length=10, choices=ESTADO_PAGO_CHOICES, default='Pendiente', verbose_name="Estado del Pago")
    notas = models.TextField(blank=True, null=True, verbose_name="Notas Adicionales")
    
    def __str__(self):
        return f"{self.miembro} - {self.tipo_membresia} ({self.fecha_inicio} al {self.fecha_vencimiento})"
    
    class Meta:
        verbose_name = "Membresía"
        verbose_name_plural = "Membresías"


class Pago(models.Model):
    membresia = models.ForeignKey(Membresia, on_delete=models.CASCADE, verbose_name="Membresía Asociada")
    miembro = models.ForeignKey(Miembro, on_delete=models.CASCADE, verbose_name="Miembro que Paga")
    fecha_pago = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora del Pago")
    monto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto Pagado")
    metodo_pago = models.ForeignKey(MetodoPago, on_delete=models.PROTECT, verbose_name="Método de Pago")
    banco = models.ForeignKey(Banco, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Banco (Opcional)")
    referencia_pago = models.CharField(max_length=100, blank=True, null=True, verbose_name="Referencia/Nº Transacción")
    registrado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Registrado por Admin")
    notas = models.TextField(blank=True, null=True, verbose_name="Notas del Pago")
    
    def __str__(self):
        return f"Pago de {self.miembro} - {self.monto} - {self.fecha_pago.strftime('%d/%m/%Y')}"
    
    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"


class AsignacionEntrenador(models.Model):
    miembro = models.ForeignKey(Miembro, on_delete=models.CASCADE, verbose_name="Miembro")
    entrenador = models.ForeignKey(Entrenador, on_delete=models.CASCADE, verbose_name="Entrenador Asignado")
    fecha_asignacion = models.DateField(auto_now_add=True, verbose_name="Fecha de Asignación")
    notas_asignacion = models.TextField(blank=True, null=True, verbose_name="Notas")
    
    def __str__(self):
        return f"{self.miembro} - {self.entrenador}"
    
    class Meta:
        verbose_name = "Asignación de Entrenador"
        verbose_name_plural = "Asignaciones de Entrenadores"
        unique_together = ('miembro', 'entrenador')


class RegistroAcceso(models.Model):
    TIPO_ACCESO_CHOICES = [
        ('Entrada', 'Entrada'),
        ('Salida', 'Salida'),
    ]
    
    RESULTADO_VERIFICACION_CHOICES = [
        ('Permitido', 'Permitido'),
        ('Denegado - Vencido', 'Denegado - Vencido'),
        ('Denegado - No Encontrado', 'Denegado - No Encontrado'),
        ('Denegado - Sin Pago', 'Denegado - Sin Pago'),
        ('Denegado - Otro', 'Denegado - Otro'),
    ]
    
    miembro = models.ForeignKey(Miembro, on_delete=models.CASCADE, verbose_name="Miembro")
    fecha_hora_intento = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora del Intento")
    tipo_acceso = models.CharField(max_length=10, choices=TIPO_ACCESO_CHOICES, verbose_name="Tipo de Acceso")
    resultado_verificacion = models.CharField(max_length=30, choices=RESULTADO_VERIFICACION_CHOICES, verbose_name="Resultado")
    punto_acceso = models.CharField(max_length=50, blank=True, null=True, verbose_name="Punto de Acceso")
    
    def __str__(self):
        return f"{self.miembro} - {self.tipo_acceso} - {self.fecha_hora_intento.strftime('%d/%m/%Y %H:%M')}"
    
    class Meta:
        verbose_name = "Registro de Acceso"
        verbose_name_plural = "Registros de Acceso"


class TipoClase(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    color_hex = models.CharField(max_length=7, blank=True, null=True, verbose_name="Color (Hex)")
    activo = models.BooleanField(default=True, verbose_name="¿Activo?")
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Tipo de Clase"
        verbose_name_plural = "Tipos de Clases"


class HorarioClase(models.Model):
    DIA_SEMANA_CHOICES = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    
    tipo_clase = models.ForeignKey(TipoClase, on_delete=models.CASCADE, verbose_name="Tipo de Clase")
    entrenador = models.ForeignKey(Entrenador, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Entrenador")
    dia_semana = models.IntegerField(choices=DIA_SEMANA_CHOICES, verbose_name="Día de la Semana")
    hora_inicio = models.TimeField(verbose_name="Hora de Inicio")
    hora_fin = models.TimeField(verbose_name="Hora de Fin")
    capacidad_maxima = models.PositiveIntegerField(blank=True, null=True, verbose_name="Capacidad Máxima")
    activo = models.BooleanField(default=True, verbose_name="¿Activo?")
    
    def __str__(self):
        return f"{self.tipo_clase} - {self.get_dia_semana_display()} {self.hora_inicio.strftime('%H:%M')}"
    
    class Meta:
        verbose_name = "Horario de Clase"
        verbose_name_plural = "Horarios de Clases"
