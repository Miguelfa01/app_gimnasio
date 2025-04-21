from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import (
    Objetivo, MetodoPago, Banco, Entrenador, TipoMembresia,
    Miembro, Membresia, Pago, AsignacionEntrenador,
    RegistroAcceso, TipoClase, HorarioClase
)
from .forms import MiembroForm, ObjetivoForm

# Create your views here.

# Vista de login
def login_view(request):
    if request.user.is_authenticated:
        return redirect('app_gimnasio:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next', 'app_gimnasio:dashboard')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Verificar si hay una URL de redirección
            if next_url and next_url != 'None':
                return redirect(next_url)
            return redirect('app_gimnasio:dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos. Por favor, intente nuevamente.')
    
    return render(request, 'app_gimnasio/login.html', {'next': request.GET.get('next')})

# Vista de logout
def logout_view(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('app_gimnasio:login')

@login_required
def dashboard(request):
    # Fecha actual
    hoy = timezone.now().date()
    
    # Miembros activos (con membresía activa)
    miembros_activos = Miembro.objects.filter(membresia__activa=True, membresia__fecha_vencimiento__gte=hoy).distinct().count()
    
    # Membresías activas
    membresias_activas = Membresia.objects.filter(activa=True, fecha_vencimiento__gte=hoy).count()
    
    # Pagos del mes actual
    inicio_mes = hoy.replace(day=1)
    pagos_mes = Pago.objects.filter(fecha_pago__date__gte=inicio_mes, fecha_pago__date__lte=hoy).count()
    
    # Membresías que vencen en los próximos 7 días
    fecha_limite = hoy + timedelta(days=7)
    vencen_pronto = Membresia.objects.filter(activa=True, fecha_vencimiento__gt=hoy, fecha_vencimiento__lte=fecha_limite).count()
    
    # Accesos recientes (últimos 10)
    accesos_recientes = RegistroAcceso.objects.all().order_by('-fecha_hora_intento')[:10]
    
    # Membresías próximas a vencer (próximos 7 días)
    membresias_vencen_pronto = Membresia.objects.filter(
        activa=True, 
        fecha_vencimiento__gt=hoy, 
        fecha_vencimiento__lte=fecha_limite
    ).order_by('fecha_vencimiento')[:10]
    
    # Clases de hoy
    dia_semana = hoy.weekday()  # 0 = Lunes, 6 = Domingo
    clases_hoy = HorarioClase.objects.filter(dia_semana=dia_semana, activo=True).order_by('hora_inicio')
    
    context = {
        'miembros_activos': miembros_activos,
        'membresias_activas': membresias_activas,
        'pagos_mes': pagos_mes,
        'vencen_pronto': vencen_pronto,
        'accesos_recientes': accesos_recientes,
        'membresias_vencen_pronto': membresias_vencen_pronto,
        'clases_hoy': clases_hoy,
    }
    
    return render(request, 'app_gimnasio/dashboard.html', context)

# API para verificación de acceso
def verificar_acceso_api(request):
    if request.method == 'POST':
        id_huella = request.POST.get('id_huella')
        tipo_acceso = request.POST.get('tipo_acceso', 'Entrada')
        punto_acceso = request.POST.get('punto_acceso', 'Principal')
        
        # Buscar miembro por ID de huella
        try:
            miembro = Miembro.objects.get(id_huella=id_huella)
            
            # Verificar si tiene membresía activa
            hoy = timezone.now().date()
            tiene_membresia_activa = Membresia.objects.filter(
                miembro=miembro,
                activa=True,
                fecha_vencimiento__gte=hoy
            ).exists()
            
            # Verificar si la membresía está pagada
            membresia_pagada = False
            if tiene_membresia_activa:
                membresia = Membresia.objects.filter(
                    miembro=miembro,
                    activa=True,
                    fecha_vencimiento__gte=hoy
                ).first()
                
                membresia_pagada = membresia.estado_pago == 'Pagado'
            
            # Determinar resultado
            if tiene_membresia_activa and membresia_pagada:
                resultado = 'Permitido'
            elif tiene_membresia_activa and not membresia_pagada:
                resultado = 'Denegado - Sin Pago'
            else:
                resultado = 'Denegado - Vencido'
                
        except Miembro.DoesNotExist:
            miembro = None
            resultado = 'Denegado - No Encontrado'
        
        # Registrar el intento de acceso
        if miembro:
            RegistroAcceso.objects.create(
                miembro=miembro,
                tipo_acceso=tipo_acceso,
                resultado_verificacion=resultado,
                punto_acceso=punto_acceso
            )
        
        # Devolver respuesta
        response_data = {
            'resultado': resultado,
            'miembro': miembro.nombre_completo() if miembro else None,
            'fecha_hora': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        return JsonResponse(response_data)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

# Vistas para Miembros
@login_required
def miembro_list(request):
    # Optimizamos la consulta con prefetch_related para cargar los objetivos relacionados
    miembros = Miembro.objects.prefetch_related('objetivos').all().order_by('apellido', 'nombre')
    
    # Agregamos información sobre membresías activas
    hoy = timezone.now().date()
    miembros_con_membresia = Membresia.objects.filter(
        activa=True, 
        fecha_vencimiento__gte=hoy
    ).values_list('miembro_id', flat=True)
    
    # Pasamos el contexto al template
    context = {
        'miembros': miembros,
        'miembros_con_membresia': miembros_con_membresia,
        'total_miembros': miembros.count()
    }
    
    return render(request, 'app_gimnasio/miembro_list.html', context)

@login_required
def miembro_detail(request, pk):
    miembro = get_object_or_404(Miembro, pk=pk)
    
    # Verificar si tiene membresía activa
    hoy = timezone.now().date()
    tiene_membresia_activa = Membresia.objects.filter(
        miembro=miembro,
        activa=True,
        fecha_vencimiento__gte=hoy
    ).exists()
    
    membresias = Membresia.objects.filter(miembro=miembro).order_by('-fecha_inicio')
    pagos = Pago.objects.filter(miembro=miembro).order_by('-fecha_pago')
    asignaciones = AsignacionEntrenador.objects.filter(miembro=miembro)
    accesos = RegistroAcceso.objects.filter(miembro=miembro).order_by('-fecha_hora_intento')[:20]
    
    context = {
        'miembro': miembro,
        'tiene_membresia_activa': tiene_membresia_activa,
        'membresias': membresias,
        'pagos': pagos,
        'asignaciones': asignaciones,
        'accesos': accesos,
    }
    
    return render(request, 'app_gimnasio/miembro_detail.html', context)

# Vistas para Membresías
@login_required
def membresia_list(request):
    vencen_pronto = request.GET.get('vencen_pronto', False)
    
    if vencen_pronto:
        hoy = timezone.now().date()
        fecha_limite = hoy + timedelta(days=7)
        membresias = Membresia.objects.filter(
            activa=True, 
            fecha_vencimiento__gt=hoy, 
            fecha_vencimiento__lte=fecha_limite
        ).order_by('fecha_vencimiento')
    else:
        membresias = Membresia.objects.filter(activa=True).order_by('-fecha_inicio')
    
    return render(request, 'app_gimnasio/membresia_list.html', {'membresias': membresias})

# Vistas para Pagos
@login_required
def pago_list(request):
    pagos = Pago.objects.all().order_by('-fecha_pago')
    return render(request, 'app_gimnasio/pago_list.html', {'pagos': pagos})

# Vistas para Entrenadores
@login_required
def entrenador_list(request):
    entrenadores = Entrenador.objects.all().order_by('apellido', 'nombre')
    return render(request, 'app_gimnasio/entrenador_list.html', {'entrenadores': entrenadores})

# Vistas para Asignaciones de Entrenadores
@login_required
def asignacion_list(request):
    asignaciones = AsignacionEntrenador.objects.all().order_by('-fecha_asignacion')
    return render(request, 'app_gimnasio/asignacion_list.html', {'asignaciones': asignaciones})

# Vistas para Tipos de Clases
@login_required
def tipo_clase_list(request):
    tipos_clase = TipoClase.objects.all().order_by('nombre')
    return render(request, 'app_gimnasio/tipo_clase_list.html', {'tipos_clase': tipos_clase})

# Vistas para Horarios de Clases
@login_required
def horario_clase_list(request):
    horarios = HorarioClase.objects.all().order_by('dia_semana', 'hora_inicio')
    return render(request, 'app_gimnasio/horario_clase_list.html', {'horarios': horarios})

# Vistas para Registros de Acceso
@login_required
def registro_acceso_list(request):
    registros = RegistroAcceso.objects.all().order_by('-fecha_hora_intento')
    return render(request, 'app_gimnasio/registro_acceso_list.html', {'registros': registros})

# Vistas para Objetivos
@login_required
def objetivo_list(request):
    objetivos = Objetivo.objects.all().order_by('nombre')
    return render(request, 'app_gimnasio/objetivo_list.html', {'objetivos': objetivos})

# Vistas para Métodos de Pago
@login_required
def metodo_pago_list(request):
    metodos_pago = MetodoPago.objects.all().order_by('nombre')
    return render(request, 'app_gimnasio/metodo_pago_list.html', {'metodos_pago': metodos_pago})

# Vistas para Bancos
@login_required
def banco_list(request):
    bancos = Banco.objects.all().order_by('nombre')
    return render(request, 'app_gimnasio/banco_list.html', {'bancos': bancos})

# Placeholder para las vistas de creación, actualización y eliminación
# Estas vistas se implementarán más adelante con formularios

@login_required
def miembro_create(request):
    if request.method == 'POST':
        form = MiembroForm(request.POST, request.FILES)
        if form.is_valid():
            miembro = form.save()
            messages.success(request, f'Miembro {miembro.nombre} {miembro.apellido} creado exitosamente.')
            return redirect('app_gimnasio:miembro_list')
    else:
        form = MiembroForm()
    
    return render(request, 'app_gimnasio/miembro_form.html', {'form': form})

@login_required
def miembro_update(request, pk):
    miembro = get_object_or_404(Miembro, pk=pk)
    
    if request.method == 'POST':
        form = MiembroForm(request.POST, request.FILES, instance=miembro)
        if form.is_valid():
            miembro = form.save()
            messages.success(request, f'Miembro {miembro.nombre} {miembro.apellido} actualizado exitosamente.')
            return redirect('app_gimnasio:miembro_detail', pk=miembro.pk)
    else:
        form = MiembroForm(instance=miembro)
    
    return render(request, 'app_gimnasio/miembro_form.html', {'form': form})

@login_required
def miembro_delete(request, pk):
    miembro = get_object_or_404(Miembro, pk=pk)
    
    if request.method == 'POST':
        # Guardar el nombre para el mensaje de éxito
        nombre_completo = f'{miembro.nombre} {miembro.apellido}'
        
        # Eliminar el miembro
        miembro.delete()
        
        messages.success(request, f'Miembro {nombre_completo} eliminado exitosamente.')
        return redirect('app_gimnasio:miembro_list')
    
    return render(request, 'app_gimnasio/miembro_confirm_delete.html', {'miembro': miembro})

# Importar vistas de membresía desde el archivo views_membresia.py
from .views_membresia import membresia_list as membresia_list_view
from .views_membresia import membresia_detail as membresia_detail_view
from .views_membresia import membresia_create as membresia_create_view
from .views_membresia import membresia_update as membresia_update_view
from .views_membresia import membresia_delete as membresia_delete_view

@login_required
def membresia_list(request):
    return membresia_list_view(request)

@login_required
def membresia_create(request):
    return membresia_create_view(request)

@login_required
def membresia_detail(request, pk):
    return membresia_detail_view(request, pk)

@login_required
def membresia_update(request, pk):
    return membresia_update_view(request, pk)

@login_required
def pago_create(request):
    # Placeholder
    return render(request, 'app_gimnasio/placeholder.html', {'mensaje': 'Crear Pago - Funcionalidad en desarrollo'})

@login_required
def entrenador_create(request):
    # Placeholder
    return render(request, 'app_gimnasio/placeholder.html', {'mensaje': 'Crear Entrenador - Funcionalidad en desarrollo'})

@login_required
def membresia_delete(request, pk):
    return membresia_delete_view(request, pk)

@login_required
def pago_detail(request, pk):
    # Placeholder
    return render(request, 'app_gimnasio/placeholder.html', {'mensaje': 'Detalle de Pago - Funcionalidad en desarrollo'})

@login_required
@login_required
def entrenador_detail(request, pk):
    # Placeholder
    return render(request, 'app_gimnasio/placeholder.html', {'mensaje': 'Detalle de Entrenador - Funcionalidad en desarrollo'})

@login_required
def entrenador_update(request, pk):
    # Placeholder
    return render(request, 'app_gimnasio/placeholder.html', {'mensaje': 'Actualizar Entrenador - Funcionalidad en desarrollo'})

@login_required
def entrenador_delete(request, pk):
    # Placeholder
    return render(request, 'app_gimnasio/placeholder.html', {'mensaje': 'Eliminar Entrenador - Funcionalidad en desarrollo'})

@login_required
def asignacion_create(request):
    # Placeholder
    return render(request, 'app_gimnasio/placeholder.html', {'mensaje': 'Crear Asignación - Funcionalidad en desarrollo'})

@login_required
def asignacion_delete(request, pk):
    # Placeholder
    return render(request, 'app_gimnasio/placeholder.html', {'mensaje': 'Eliminar Asignación - Funcionalidad en desarrollo'})

@login_required
def tipo_clase_create(request):
    # Placeholder
    return render(request, 'app_gimnasio/placeholder.html', {'mensaje': 'Crear Tipo de Clase - Funcionalidad en desarrollo'})

@login_required
def tipo_clase_update(request, pk):
    # Placeholder
    return render(request, 'app_gimnasio/placeholder.html', {'mensaje': 'Actualizar Tipo de Clase - Funcionalidad en desarrollo'})

@login_required
def tipo_clase_delete(request, pk):
    # Placeholder
    return render(request, 'app_gimnasio/placeholder.html', {'mensaje': 'Eliminar Tipo de Clase - Funcionalidad en desarrollo'})

@login_required
def horario_clase_create(request):
    # Placeholder
    return render(request, 'app_gimnasio/placeholder.html', {'mensaje': 'Crear Horario de Clase - Funcionalidad en desarrollo'})

@login_required
def horario_clase_update(request, pk):
    # Placeholder
    return render(request, 'app_gimnasio/placeholder.html', {'mensaje': 'Actualizar Horario de Clase - Funcionalidad en desarrollo'})

@login_required
def horario_clase_delete(request, pk):
    # Placeholder
    return render(request, 'app_gimnasio/placeholder.html', {'mensaje': 'Eliminar Horario de Clase - Funcionalidad en desarrollo'})

# --- OBJETIVOS (CRUD real, no placeholder) ---
from .forms import ObjetivoForm
from .models import Objetivo
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, get_object_or_404, redirect

@login_required
@permission_required('app_gimnasio.add_objetivo', raise_exception=True)
def objetivo_create(request):
    if request.method == 'POST':
        form = ObjetivoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('app_gimnasio:objetivo_list')
    else:
        form = ObjetivoForm()
    return render(request, 'app_gimnasio/objetivo_form.html', {'form': form, 'title': 'Nuevo Objetivo'})

@login_required
@permission_required('app_gimnasio.change_objetivo', raise_exception=True)
def objetivo_update(request, pk):
    objetivo = get_object_or_404(Objetivo, pk=pk)
    if request.method == 'POST':
        form = ObjetivoForm(request.POST, instance=objetivo)
        if form.is_valid():
            form.save()
            return redirect('app_gimnasio:objetivo_list')
    else:
        form = ObjetivoForm(instance=objetivo)
    return render(request, 'app_gimnasio/objetivo_form.html', {'form': form, 'title': 'Editar Objetivo'})

@login_required
@permission_required('app_gimnasio.delete_objetivo', raise_exception=True)
def objetivo_delete(request, pk):
    objetivo = get_object_or_404(Objetivo, pk=pk)
    if request.method == 'POST':
        objetivo.delete()
        return redirect('app_gimnasio:objetivo_list')
    return render(request, 'app_gimnasio/objetivo_confirm_delete.html', {'objetivo': objetivo})

@login_required
def metodo_pago_create(request):
    # Placeholder
    return render(request, 'app_gimnasio/placeholder.html', {'mensaje': 'Crear Método de Pago - Funcionalidad en desarrollo'})

@login_required
def metodo_pago_update(request, pk):
    # Placeholder
    return render(request, 'app_gimnasio/placeholder.html', {'mensaje': 'Actualizar Método de Pago - Funcionalidad en desarrollo'})

@login_required
def metodo_pago_delete(request, pk):
    # Placeholder
    return render(request, 'app_gimnasio/placeholder.html', {'mensaje': 'Eliminar Método de Pago - Funcionalidad en desarrollo'})

@login_required
def banco_create(request):
    # Placeholder
    return render(request, 'app_gimnasio/placeholder.html', {'mensaje': 'Crear Banco - Funcionalidad en desarrollo'})

@login_required
def banco_update(request, pk):
    # Placeholder
    return render(request, 'app_gimnasio/placeholder.html', {'mensaje': 'Actualizar Banco - Funcionalidad en desarrollo'})

@login_required
def banco_delete(request, pk):
    # Placeholder
    return render(request, 'app_gimnasio/placeholder.html', {'mensaje': 'Eliminar Banco - Funcionalidad en desarrollo'})
