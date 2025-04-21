from django.urls import path
from . import views
from .views_membresia import membresia_renovar
from .views_pago import pago_list, pago_detail, pago_create, pago_update, pago_delete, generar_recibo, reporte_pagos
from .views_api import miembro_membresias, membresia_detalle, membresia_pagos, metodo_pago_detalle, miembros_autocomplete
from .views_reporte import reporte_miembros_activos_inactivos, exportar_miembros_excel, exportar_miembros_pdf

app_name = 'app_gimnasio'

urlpatterns = [
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Miembros
    path('miembros/', views.miembro_list, name='miembro_list'),
    path('miembros/nuevo/', views.miembro_create, name='miembro_create'),
    path('miembros/<int:pk>/', views.miembro_detail, name='miembro_detail'),
    path('miembros/<int:pk>/editar/', views.miembro_update, name='miembro_update'),
    path('miembros/<int:pk>/eliminar/', views.miembro_delete, name='miembro_delete'),
    
    # Membresías
    path('membresias/', views.membresia_list, name='membresia_list'),
    path('membresias/nueva/', views.membresia_create, name='membresia_create'),
    path('membresias/<int:pk>/', views.membresia_detail, name='membresia_detail'),
    path('membresias/<int:pk>/editar/', views.membresia_update, name='membresia_update'),
    path('membresias/<int:pk>/eliminar/', views.membresia_delete, name='membresia_delete'),
    path('membresias/<int:pk>/renovar/', membresia_renovar, name='membresia_renovar'),
    
    # Pagos
    path('pagos/', pago_list, name='pago_list'),
    path('pagos/nuevo/', pago_create, name='pago_create'),
    path('pagos/<int:pk>/', pago_detail, name='pago_detail'),
    path('pagos/<int:pk>/editar/', pago_update, name='pago_update'),
    path('pagos/<int:pk>/eliminar/', pago_delete, name='pago_delete'),
    path('pagos/<int:pk>/recibo/', generar_recibo, name='generar_recibo'),
    path('pagos/reportes/', reporte_pagos, name='reporte_pagos'),
    
    # API para el módulo de pagos
    path('api/miembro/<int:miembro_id>/membresias/', miembro_membresias, name='api_miembro_membresias'),
    path('api/membresia/<int:membresia_id>/', membresia_detalle, name='api_membresia_detalle'),
    path('api/membresia/<int:membresia_id>/pagos/', membresia_pagos, name='api_membresia_pagos'),
    path('api/metodo_pago/<int:metodo_id>/', metodo_pago_detalle, name='api_metodo_pago_detalle'),
    path('api/miembros_autocomplete/', miembros_autocomplete, name='api_miembros_autocomplete'),
    
    # Entrenadores
    path('entrenadores/', views.entrenador_list, name='entrenador_list'),
    path('entrenadores/nuevo/', views.entrenador_create, name='entrenador_create'),
    path('entrenadores/<int:pk>/', views.entrenador_detail, name='entrenador_detail'),
    path('entrenadores/<int:pk>/editar/', views.entrenador_update, name='entrenador_update'),
    path('entrenadores/<int:pk>/eliminar/', views.entrenador_delete, name='entrenador_delete'),
    
    # Asignaciones de Entrenadores
    path('asignaciones/', views.asignacion_list, name='asignacion_list'),
    path('asignaciones/nueva/', views.asignacion_create, name='asignacion_create'),
    path('asignaciones/<int:pk>/eliminar/', views.asignacion_delete, name='asignacion_delete'),
    
    # Clases
    path('clases/tipos/', views.tipo_clase_list, name='tipo_clase_list'),
    path('clases/tipos/nuevo/', views.tipo_clase_create, name='tipo_clase_create'),
    path('clases/tipos/<int:pk>/editar/', views.tipo_clase_update, name='tipo_clase_update'),
    path('clases/tipos/<int:pk>/eliminar/', views.tipo_clase_delete, name='tipo_clase_delete'),
    
    # Horarios de Clases
    path('clases/horarios/', views.horario_clase_list, name='horario_clase_list'),
    path('clases/horarios/nuevo/', views.horario_clase_create, name='horario_clase_create'),
    path('clases/horarios/<int:pk>/editar/', views.horario_clase_update, name='horario_clase_update'),
    path('clases/horarios/<int:pk>/eliminar/', views.horario_clase_delete, name='horario_clase_delete'),
    
    # Registros de Acceso
    path('accesos/', views.registro_acceso_list, name='registro_acceso_list'),
    
    # Objetivos
    path('objetivos/', views.objetivo_list, name='objetivo_list'),
    # Ruta deshabilitada: path('objetivos/nuevo/', views.objetivo_create, name='objetivo_create'),
    path('objetivos/<int:pk>/editar/', views.objetivo_update, name='objetivo_update'),
    path('objetivos/<int:pk>/eliminar/', views.objetivo_delete, name='objetivo_delete'),
    
    # Configuración
    path('configuracion/metodos-pago/', views.metodo_pago_list, name='metodo_pago_list'),
    path('configuracion/metodos-pago/nuevo/', views.metodo_pago_create, name='metodo_pago_create'),
    path('configuracion/metodos-pago/<int:pk>/editar/', views.metodo_pago_update, name='metodo_pago_update'),
    path('configuracion/metodos-pago/<int:pk>/eliminar/', views.metodo_pago_delete, name='metodo_pago_delete'),
    
    path('configuracion/bancos/', views.banco_list, name='banco_list'),
    path('configuracion/bancos/nuevo/', views.banco_create, name='banco_create'),
    path('configuracion/bancos/<int:pk>/editar/', views.banco_update, name='banco_update'),
    path('configuracion/bancos/<int:pk>/eliminar/', views.banco_delete, name='banco_delete'),
    
    # Reportes
    path('reportes/miembros/activos-inactivos/', reporte_miembros_activos_inactivos, name='reporte_miembros_activos_inactivos'),
    path('reporte/exportar_excel/', exportar_miembros_excel, name='exportar_miembros_excel'),
    path('reporte/exportar_pdf/', exportar_miembros_pdf, name='exportar_miembros_pdf'),
    
    # API para verificación de acceso
    path('api/verificar-acceso/', views.verificar_acceso_api, name='verificar_acceso_api'),
]
