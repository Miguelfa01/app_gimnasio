from django.contrib import admin
from .models import (
    Objetivo, MetodoPago, Banco, Entrenador, TipoMembresia,
    Miembro, Membresia, Pago, AsignacionEntrenador,
    RegistroAcceso, TipoClase, HorarioClase
)

# Register your models here.

@admin.register(Objetivo)
class ObjetivoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)

@admin.register(MetodoPago)
class MetodoPagoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'requiere_banco', 'activo')
    list_filter = ('requiere_banco', 'activo')
    search_fields = ('nombre',)

@admin.register(Banco)
class BancoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo_swift', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'codigo_swift')

@admin.register(Entrenador)
class EntrenadorAdmin(admin.ModelAdmin):
    list_display = ('cedula', 'nombre', 'apellido', 'especialidad', 'activo')
    list_filter = ('activo', 'especialidad')
    search_fields = ('cedula', 'nombre', 'apellido', 'especialidad')

@admin.register(TipoMembresia)
class TipoMembresiaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'duracion_dias', 'precio_estandar', 'permite_acceso_clases', 'activo')
    list_filter = ('permite_acceso_clases', 'activo')
    search_fields = ('nombre',)

class MiembroObjetivoInline(admin.TabularInline):
    model = Miembro.objetivos.through
    extra = 1

@admin.register(Miembro)
class MiembroAdmin(admin.ModelAdmin):
    list_display = ('cedula', 'nombre', 'apellido', 'telefono', 'correo_electronico', 'fecha_registro')
    list_filter = ('fecha_registro',)
    search_fields = ('cedula', 'nombre', 'apellido', 'telefono', 'correo_electronico')
    fieldsets = (
        ('Información Personal', {
            'fields': ('cedula', 'nombre', 'apellido', 'fecha_nacimiento', 'telefono', 'correo_electronico', 'direccion', 'foto')
        }),
        ('Información Médica y de Emergencia', {
            'fields': ('condicion_medica', 'contacto_emergencia_nombre', 'contacto_emergencia_parentesco', 'contacto_emergencia_telefono')
        }),
        ('Información de Acceso', {
            'fields': ('id_huella',)
        }),
        ('Notas', {
            'fields': ('notas',)
        }),
    )
    inlines = [MiembroObjetivoInline]
    exclude = ('objetivos',)

@admin.register(Membresia)
class MembresiaAdmin(admin.ModelAdmin):
    list_display = ('miembro', 'tipo_membresia', 'fecha_inicio', 'fecha_vencimiento', 'precio_pagado', 'estado_pago', 'activa')
    list_filter = ('tipo_membresia', 'estado_pago', 'activa', 'fecha_inicio', 'fecha_vencimiento')
    search_fields = ('miembro__nombre', 'miembro__apellido', 'miembro__cedula')
    date_hierarchy = 'fecha_inicio'

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('miembro', 'membresia', 'fecha_pago', 'monto', 'metodo_pago', 'banco', 'registrado_por')
    list_filter = ('metodo_pago', 'banco', 'fecha_pago')
    search_fields = ('miembro__nombre', 'miembro__apellido', 'miembro__cedula', 'referencia_pago')
    date_hierarchy = 'fecha_pago'

@admin.register(AsignacionEntrenador)
class AsignacionEntrenadorAdmin(admin.ModelAdmin):
    list_display = ('miembro', 'entrenador', 'fecha_asignacion')
    list_filter = ('entrenador', 'fecha_asignacion')
    search_fields = ('miembro__nombre', 'miembro__apellido', 'entrenador__nombre', 'entrenador__apellido')
    date_hierarchy = 'fecha_asignacion'

@admin.register(RegistroAcceso)
class RegistroAccesoAdmin(admin.ModelAdmin):
    list_display = ('miembro', 'fecha_hora_intento', 'tipo_acceso', 'resultado_verificacion', 'punto_acceso')
    list_filter = ('tipo_acceso', 'resultado_verificacion', 'fecha_hora_intento', 'punto_acceso')
    search_fields = ('miembro__nombre', 'miembro__apellido', 'miembro__cedula')
    date_hierarchy = 'fecha_hora_intento'
    readonly_fields = ('miembro', 'fecha_hora_intento', 'tipo_acceso', 'resultado_verificacion', 'punto_acceso')

@admin.register(TipoClase)
class TipoClaseAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'color_hex', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)

@admin.register(HorarioClase)
class HorarioClaseAdmin(admin.ModelAdmin):
    list_display = ('tipo_clase', 'entrenador', 'get_dia_semana_display', 'hora_inicio', 'hora_fin', 'capacidad_maxima', 'activo')
    list_filter = ('tipo_clase', 'entrenador', 'dia_semana', 'activo')
    search_fields = ('tipo_clase__nombre', 'entrenador__nombre', 'entrenador__apellido')
