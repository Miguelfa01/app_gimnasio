from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count
from django.http import HttpResponse
import csv
from datetime import timedelta
from .models import Pago, Miembro, Membresia, MetodoPago, Banco
from .forms_pago import PagoForm

@login_required
def pago_list(request):
    """Vista para listar todos los pagos."""
    # Obtener parámetros de filtro
    miembro_id = request.GET.get('miembro')
    metodo_id = request.GET.get('metodo')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Iniciar con todos los pagos
    pagos = Pago.objects.select_related('miembro', 'membresia', 'metodo_pago', 'banco').all()
    
    # Aplicar filtros si se proporcionan
    if miembro_id:
        pagos = pagos.filter(miembro_id=miembro_id)
    
    if metodo_id:
        pagos = pagos.filter(metodo_pago_id=metodo_id)
    
    if fecha_inicio:
        try:
            fecha_inicio = timezone.datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            pagos = pagos.filter(fecha_pago__date__gte=fecha_inicio)
        except ValueError:
            pass
    
    if fecha_fin:
        try:
            fecha_fin = timezone.datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            pagos = pagos.filter(fecha_pago__date__lte=fecha_fin)
        except ValueError:
            pass
    
    # Ordenar por fecha de pago (más reciente primero)
    pagos = pagos.order_by('-fecha_pago')
    
    # Calcular estadísticas
    total_pagos = pagos.count()
    suma_pagos = pagos.aggregate(total=Sum('monto'))['total'] or 0
    
    # Obtener todos los miembros y métodos de pago para los filtros
    miembros = Miembro.objects.all().order_by('apellido', 'nombre')
    metodos_pago = MetodoPago.objects.all()
    
    # Verificar si se solicitó exportar a CSV
    if 'export' in request.GET:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="pagos.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Fecha', 'Miembro', 'Membresía', 'Monto', 'Método de Pago', 'Banco', 'Referencia'])
        
        for pago in pagos:
            writer.writerow([
                pago.id,
                pago.fecha_pago.strftime('%d/%m/%Y %H:%M'),
                f"{pago.miembro.nombre} {pago.miembro.apellido}",
                pago.membresia.tipo_membresia.nombre,
                pago.monto,
                pago.metodo_pago.nombre,
                pago.banco.nombre if pago.banco else '',
                pago.referencia_pago or ''
            ])
        
        return response
    
    context = {
        'pagos': pagos,
        'total_pagos': total_pagos,
        'suma_pagos': suma_pagos,
        'miembros': miembros,
        'metodos_pago': metodos_pago,
        'filtros': {
            'miembro_id': miembro_id,
            'metodo_id': metodo_id,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin
        }
    }
    
    return render(request, 'app_gimnasio/pago_list.html', context)

@login_required
def pago_detail(request, pk):
    """Vista para ver los detalles de un pago específico."""
    pago = get_object_or_404(Pago, pk=pk)
    
    # Obtener otros pagos del mismo miembro
    otros_pagos = Pago.objects.filter(miembro=pago.miembro).exclude(pk=pk).order_by('-fecha_pago')[:5]
    
    # Obtener pagos de la misma membresía
    pagos_membresia = Pago.objects.filter(membresia=pago.membresia).order_by('-fecha_pago')
    total_pagado = pagos_membresia.aggregate(total=Sum('monto'))['total'] or 0
    saldo_pendiente = pago.membresia.precio_pagado - total_pagado
    
    # Cálculo correcto del porcentaje de progreso
    if pago.membresia.precio_pagado == 0:
        progreso_pago = 100
    else:
        progreso_pago = min(100, (total_pagado / pago.membresia.precio_pagado) * 100)
    
    context = {
        'pago': pago,
        'otros_pagos': otros_pagos,
        'pagos_membresia': pagos_membresia,
        'total_pagado': total_pagado,
        'saldo_pendiente': saldo_pendiente,
        'progreso_pago': progreso_pago
    }
    
    return render(request, 'app_gimnasio/pago_detail.html', context)

@login_required
def pago_create(request):
    """Vista para crear un nuevo pago."""
    # Obtener parámetros de la URL
    miembro_id = request.GET.get('miembro_id')
    membresia_id = request.GET.get('membresia_id')
    
    initial = {}
    
    # Pre-seleccionar miembro si se proporciona
    if miembro_id:
        try:
            miembro = Miembro.objects.get(pk=miembro_id)
            initial['miembro'] = miembro
        except Miembro.DoesNotExist:
            pass
    
    # Pre-seleccionar membresía si se proporciona
    if membresia_id:
        try:
            membresia = Membresia.objects.get(pk=membresia_id)
            initial['membresia'] = membresia
            initial['miembro'] = membresia.miembro
        except Membresia.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = PagoForm(request.POST)
        if form.is_valid():
            pago = form.save(commit=False)
            # Registrar el usuario que creó el pago
            pago.registrado_por = request.user
            pago.save()
            
            # Actualizar estado de pago de la membresía
            membresia = pago.membresia
            total_pagado = Pago.objects.filter(membresia=membresia).aggregate(total=Sum('monto'))['total'] or 0
            
            if total_pagado >= membresia.precio_pagado:
                membresia.estado_pago = 'Pagado'
            elif total_pagado > 0:
                membresia.estado_pago = 'Parcial'
            else:
                membresia.estado_pago = 'Pendiente'
            
            membresia.save()
            
            messages.success(request, f'Pago registrado exitosamente por {pago.monto}.')
            
            # Redirigir según el parámetro next o a la vista de detalle
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('app_gimnasio:pago_detail', pk=pago.pk)
    else:
        form = PagoForm(initial=initial)
    
    # Obtener todos los miembros para el selector
    miembros = Miembro.objects.all().order_by('apellido', 'nombre')
    
    context = {
        'form': form,
        'miembros': miembros,
        'initial': initial
    }
    
    return render(request, 'app_gimnasio/pago_form.html', context)

@login_required
def pago_update(request, pk):
    """Vista para actualizar un pago existente."""
    pago = get_object_or_404(Pago, pk=pk)
    
    if request.method == 'POST':
        form = PagoForm(request.POST, instance=pago)
        if form.is_valid():
            form.save()
            
            # Actualizar estado de pago de la membresía
            membresia = pago.membresia
            total_pagado = Pago.objects.filter(membresia=membresia).aggregate(total=Sum('monto'))['total'] or 0
            
            if total_pagado >= membresia.precio_pagado:
                membresia.estado_pago = 'Pagado'
            elif total_pagado > 0:
                membresia.estado_pago = 'Parcial'
            else:
                membresia.estado_pago = 'Pendiente'
            
            membresia.save()
            
            messages.success(request, f'Pago actualizado exitosamente.')
            return redirect('app_gimnasio:pago_detail', pk=pago.pk)
    else:
        form = PagoForm(instance=pago)
    
    context = {
        'form': form,
        'pago': pago
    }
    
    return render(request, 'app_gimnasio/pago_form.html', context)

@login_required
def pago_delete(request, pk):
    """Vista para eliminar un pago."""
    pago = get_object_or_404(Pago, pk=pk)
    membresia = pago.membresia
    
    if request.method == 'POST':
        # Guardar información para el mensaje
        monto = pago.monto
        miembro = f'{pago.miembro.nombre} {pago.miembro.apellido}'
        
        # Eliminar el pago
        pago.delete()
        
        # Actualizar estado de pago de la membresía
        total_pagado = Pago.objects.filter(membresia=membresia).aggregate(total=Sum('monto'))['total'] or 0
        
        if total_pagado >= membresia.precio_pagado:
            membresia.estado_pago = 'Pagado'
        elif total_pagado > 0:
            membresia.estado_pago = 'Parcial'
        else:
            membresia.estado_pago = 'Pendiente'
        
        membresia.save()
        
        messages.success(request, f'Pago de {monto} para {miembro} eliminado exitosamente.')
        return redirect('app_gimnasio:pago_list')
    
    return render(request, 'app_gimnasio/pago_confirm_delete.html', {'pago': pago})

@login_required
def generar_recibo(request, pk):
    """Vista para generar un recibo de pago."""
    pago = get_object_or_404(Pago, pk=pk)
    
    # Obtener pagos de la misma membresía
    pagos_membresia = Pago.objects.filter(membresia=pago.membresia).order_by('-fecha_pago')
    total_pagado = pagos_membresia.aggregate(total=Sum('monto'))['total'] or 0
    saldo_pendiente = pago.membresia.precio_pagado - total_pagado
    
    # Cálculo correcto del porcentaje de progreso
    if pago.membresia.precio_pagado == 0:
        progreso_pago = 100
    else:
        progreso_pago = min(100, (total_pagado / pago.membresia.precio_pagado) * 100)
    
    context = {
        'pago': pago,
        'total_pagado': total_pagado,
        'saldo_pendiente': saldo_pendiente,
        'progreso_pago': progreso_pago,
        'fecha_impresion': timezone.now()
    }
    
    return render(request, 'app_gimnasio/pago_recibo.html', context)

@login_required
def reporte_pagos(request):
    """Vista para generar reportes de pagos."""
    # Obtener parámetros
    periodo = request.GET.get('periodo', 'mes')
    metodo_id = request.GET.get('metodo')
    
    # Determinar fechas según el período
    hoy = timezone.now().date()
    
    if periodo == 'semana':
        inicio_periodo = hoy - timedelta(days=hoy.weekday())
        titulo_periodo = f"Semana del {inicio_periodo.strftime('%d/%m/%Y')} al {(inicio_periodo + timedelta(days=6)).strftime('%d/%m/%Y')}"
    elif periodo == 'mes':
        inicio_periodo = hoy.replace(day=1)
        if hoy.month == 12:
            fin_periodo = hoy.replace(year=hoy.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            fin_periodo = hoy.replace(month=hoy.month + 1, day=1) - timedelta(days=1)
        titulo_periodo = f"Mes de {inicio_periodo.strftime('%B %Y')}"
    elif periodo == 'anio':
        inicio_periodo = hoy.replace(month=1, day=1)
        fin_periodo = hoy.replace(month=12, day=31)
        titulo_periodo = f"Año {hoy.year}"
    else:  # personalizado
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        
        try:
            inicio_periodo = timezone.datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            inicio_periodo = hoy - timedelta(days=30)
            
        try:
            fin_periodo = timezone.datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            fin_periodo = hoy
            
        titulo_periodo = f"Período del {inicio_periodo.strftime('%d/%m/%Y')} al {fin_periodo.strftime('%d/%m/%Y')}"
    
    # Filtrar pagos por período
    pagos = Pago.objects.filter(fecha_pago__date__gte=inicio_periodo, fecha_pago__date__lte=fin_periodo)
    
    # Filtrar por método de pago si se especifica
    if metodo_id:
        pagos = pagos.filter(metodo_pago_id=metodo_id)
    
    # Calcular estadísticas
    total_pagos = pagos.count()
    suma_pagos = pagos.aggregate(total=Sum('monto'))['total'] or 0
    
    # Agrupar por método de pago
    pagos_por_metodo = pagos.values('metodo_pago__nombre').annotate(
        total=Sum('monto'),
        cantidad=Count('id')
    ).order_by('-total')
    
    # Agrupar por día
    pagos_por_dia = pagos.extra(select={'day': "DATE(fecha_pago)"}).values('day').annotate(
        total=Sum('monto'),
        cantidad=Count('id')
    ).order_by('day')
    
    # Obtener todos los métodos de pago para el filtro
    metodos_pago = MetodoPago.objects.all()
    
    context = {
        'pagos': pagos.order_by('-fecha_pago'),
        'total_pagos': total_pagos,
        'suma_pagos': suma_pagos,
        'pagos_por_metodo': pagos_por_metodo,
        'pagos_por_dia': pagos_por_dia,
        'metodos_pago': metodos_pago,
        'titulo_periodo': titulo_periodo,
        'filtros': {
            'periodo': periodo,
            'metodo_id': metodo_id,
            'fecha_inicio': inicio_periodo.strftime('%Y-%m-%d') if periodo == 'personalizado' else None,
            'fecha_fin': fin_periodo.strftime('%Y-%m-%d') if periodo == 'personalizado' else None
        }
    }
    
    return render(request, 'app_gimnasio/pago_reporte.html', context)
