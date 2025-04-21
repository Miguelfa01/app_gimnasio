from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import Membresia, Miembro, TipoMembresia, Pago, RegistroAcceso
from .forms_membresia import MembresiaForm

@login_required
def membresia_list(request):
    """Vista para listar todas las membresías."""
    # Obtener la fecha actual
    hoy = timezone.now().date()
    
    # Definir el período para membresías por vencer (30 días)
    fecha_limite = hoy + timedelta(days=30)
    
    # Obtener todas las membresías (excluyendo vencidas renovadas)
    membresias = Membresia.objects.select_related('miembro', 'tipo_membresia').filter(
        # Si está vencida, solo mostrar si renovada es False
        # Si no está vencida, mostrar siempre
        # Esto se filtra en el template con el atributo calculado, pero aquí lo hacemos a nivel de queryset
    ).order_by('-fecha_inicio')
    membresias = [m for m in membresias if not (m.fecha_vencimiento < hoy and m.renovada)]
    
    # Añadir atributos calculados a cada membresía
    for membresia in membresias:
        # Verificar si está vencida
        membresia.vencida = membresia.fecha_vencimiento < hoy
        
        # Verificar si está por vencer (en los próximos 30 días)
        membresia.por_vencer = (not membresia.vencida and 
                               membresia.fecha_vencimiento <= fecha_limite)
    
    # Contar membresías por estado
    activas_count = sum(1 for m in membresias if m.activa and not m.vencida)
    por_vencer_count = sum(1 for m in membresias if m.por_vencer)
    vencidas_count = sum(1 for m in membresias if m.vencida)
    total_membresias = len(membresias)
    
    context = {
        'membresias': membresias,
        'activas_count': activas_count,
        'por_vencer_count': por_vencer_count,
        'vencidas_count': vencidas_count,
        'total_membresias': total_membresias,
    }
    
    return render(request, 'app_gimnasio/membresia_list.html', context)

@login_required
def membresia_detail(request, pk):
    """Vista para ver los detalles de una membresía específica."""
    membresia = get_object_or_404(Membresia, pk=pk)
    
    # Obtener la fecha actual
    hoy = timezone.now().date()
    
    # Definir el período para membresías por vencer (30 días)
    fecha_limite = hoy + timedelta(days=30)
    
    # Calcular atributos
    membresia.vencida = membresia.fecha_vencimiento < hoy
    membresia.por_vencer = (not membresia.vencida and 
                           membresia.fecha_vencimiento <= fecha_limite)
    
    # Calcular días restantes
    if not membresia.vencida:
        dias_restantes = (membresia.fecha_vencimiento - hoy).days
    else:
        dias_restantes = 0
    
    # Obtener pagos asociados
    pagos = Pago.objects.filter(membresia=membresia).order_by('-fecha_pago')
    
    # Obtener registros de acceso del miembro durante el período de la membresía
    accesos = RegistroAcceso.objects.filter(
        miembro=membresia.miembro,
        fecha_hora_intento__date__gte=membresia.fecha_inicio,
        fecha_hora_intento__date__lte=max(hoy, membresia.fecha_vencimiento)
    ).order_by('-fecha_hora_intento')[:10]  # Mostrar solo los últimos 10
    
    context = {
        'membresia': membresia,
        'dias_restantes': dias_restantes,
        'pagos': pagos,
        'accesos': accesos,
    }
    
    return render(request, 'app_gimnasio/membresia_detail.html', context)

@login_required
def membresia_create(request):
    """Vista para crear una nueva membresía."""
    # Obtener todos los tipos de membresía para el JavaScript
    tipos_membresia = TipoMembresia.objects.all()
    
    if request.method == 'POST':
        form = MembresiaForm(request.POST)
        if form.is_valid():
            membresia = form.save()
            messages.success(request, f'Membresía creada exitosamente para {membresia.miembro.nombre} {membresia.miembro.apellido}.')
            return redirect('app_gimnasio:membresia_detail', pk=membresia.pk)
    else:
        # Preseleccionar miembro si se proporciona en la URL
        miembro_id = request.GET.get('miembro_id')
        initial = {}
        if miembro_id:
            try:
                miembro = Miembro.objects.get(pk=miembro_id)
                initial['miembro'] = miembro
            except Miembro.DoesNotExist:
                pass
        
        form = MembresiaForm(initial=initial)
    
    context = {
        'form': form,
        'tipos_membresia': tipos_membresia,
    }
    
    return render(request, 'app_gimnasio/membresia_form.html', context)

@login_required
def membresia_update(request, pk):
    """Vista para actualizar una membresía existente."""
    membresia = get_object_or_404(Membresia, pk=pk)
    tipos_membresia = TipoMembresia.objects.all()
    
    if request.method == 'POST':
        form = MembresiaForm(request.POST, instance=membresia)
        if form.is_valid():
            membresia = form.save()
            messages.success(request, f'Membresía actualizada exitosamente para {membresia.miembro.nombre} {membresia.miembro.apellido}.')
            return redirect('app_gimnasio:membresia_detail', pk=membresia.pk)
    else:
        form = MembresiaForm(instance=membresia)
    
    context = {
        'form': form,
        'tipos_membresia': tipos_membresia,
    }
    
    return render(request, 'app_gimnasio/membresia_form.html', context)

@login_required
def membresia_delete(request, pk):
    """Vista para eliminar una membresía."""
    membresia = get_object_or_404(Membresia, pk=pk)
    
    if request.method == 'POST':
        # Guardar información para el mensaje
        nombre_miembro = f'{membresia.miembro.nombre} {membresia.miembro.apellido}'
        tipo_membresia = membresia.tipo_membresia.nombre
        
        # Eliminar la membresía
        membresia.delete()
        
        messages.success(request, f'Membresía {tipo_membresia} de {nombre_miembro} eliminada exitosamente.')
        return redirect('app_gimnasio:membresia_list')
    
    return render(request, 'app_gimnasio/membresia_confirm_delete.html', {'membresia': membresia})

@login_required
def membresia_renovar(request, pk):
    """Vista para renovar una membresía existente."""
    membresia_original = get_object_or_404(Membresia, pk=pk)
    # Obtener todos los tipos de membresía para el JavaScript
    tipos_membresia = TipoMembresia.objects.all()
    
    # Calcular la fecha de inicio para la renovación
    hoy = timezone.now().date()
    if membresia_original.fecha_vencimiento > hoy:
        # Si aún no ha vencido, la nueva comienza después del vencimiento
        fecha_inicio = membresia_original.fecha_vencimiento + timedelta(days=1)
    else:
        # Si ya venció, la nueva comienza hoy
        fecha_inicio = hoy
    
    if request.method == 'POST':
        form = MembresiaForm(request.POST)
        if form.is_valid():
            nueva_membresia = form.save()
            # Marcar la membresía original como renovada
            membresia_original.renovada = True
            membresia_original.save()
            messages.success(request, 'Membresía renovada exitosamente.')
            return redirect('app_gimnasio:membresia_detail', pk=nueva_membresia.pk)
    else:
        # Pre-llenar el formulario con datos de la membresía original
        # Calcular la fecha de vencimiento basándose en la fecha de inicio y la duración del tipo de membresía
        fecha_vencimiento = fecha_inicio + timedelta(days=membresia_original.tipo_membresia.duracion_dias)
        
        initial = {
            'miembro': membresia_original.miembro,
            'tipo_membresia': membresia_original.tipo_membresia,
            'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),  # Formato YYYY-MM-DD para el widget HTML5 date
            'fecha_vencimiento': fecha_vencimiento.strftime('%Y-%m-%d'),  # Formato YYYY-MM-DD para el widget HTML5 date
            'precio': membresia_original.tipo_membresia.precio_estandar,
        }
        form = MembresiaForm(initial=initial)
    
    context = {
        'form': form,
        'tipos_membresia': tipos_membresia,
        'es_renovacion': True,
        'membresia_original': membresia_original
    }
    
    return render(request, 'app_gimnasio/membresia_form.html', context)
