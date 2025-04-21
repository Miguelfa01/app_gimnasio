from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Sum
from django.utils import timezone
from .models import Miembro, Membresia, TipoMembresia, MetodoPago, Banco, Pago, Objetivo
from .forms import ObjetivoForm
from .models import MetodoPago, Banco, Pago

@login_required
def miembro_membresias(request, miembro_id):
    """API para obtener las membresías de un miembro."""
    miembro = get_object_or_404(Miembro, pk=miembro_id)
    hoy = timezone.now().date()
    membresias = Membresia.objects.filter(
        miembro=miembro,
        activa=True,
        fecha_vencimiento__gte=hoy,
        renovada=False
    ).select_related('tipo_membresia')
    
    data = []
    for membresia in membresias:
        data.append({
            'id': membresia.id,
            'tipo_membresia': {
                'id': membresia.tipo_membresia.id,
                'nombre': membresia.tipo_membresia.nombre,
                'duracion_dias': membresia.tipo_membresia.duracion_dias,
                'precio_estandar': float(membresia.tipo_membresia.precio_estandar)
            },
            'fecha_inicio': membresia.fecha_inicio.strftime('%Y-%m-%d'),
            'fecha_vencimiento': membresia.fecha_vencimiento.strftime('%Y-%m-%d'),
            'precio_pagado': float(membresia.precio_pagado),
            'estado_pago': membresia.estado_pago
        })
    
    return JsonResponse(data, safe=False)

@login_required
def membresia_detalle(request, membresia_id):
    """API para obtener los detalles de una membresía."""
    membresia = get_object_or_404(Membresia, pk=membresia_id)
    
    # Calcular total pagado
    pagos = Pago.objects.filter(membresia=membresia)
    total_pagado = pagos.aggregate(total=Sum('monto'))['total'] or 0
    
    data = {
        'id': membresia.id,
        'miembro': {
            'id': membresia.miembro.id,
            'nombre': membresia.miembro.nombre,
            'apellido': membresia.miembro.apellido,
            'cedula': membresia.miembro.cedula
        },
        'tipo_membresia': {
            'id': membresia.tipo_membresia.id,
            'nombre': membresia.tipo_membresia.nombre,
            'duracion_dias': membresia.tipo_membresia.duracion_dias,
            'precio_estandar': float(membresia.tipo_membresia.precio_estandar)
        },
        'fecha_inicio': membresia.fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_vencimiento': membresia.fecha_vencimiento.strftime('%Y-%m-%d'),
        'precio_pagado': float(membresia.precio_pagado),
        'estado_pago': membresia.estado_pago,
        'total_pagado': float(total_pagado)
    }
    
    return JsonResponse(data)

@login_required
def membresia_pagos(request, membresia_id):
    """API para obtener los pagos de una membresía."""
    membresia = get_object_or_404(Membresia, pk=membresia_id)
    pagos = Pago.objects.filter(membresia=membresia).select_related('metodo_pago', 'banco')
    
    data = []
    for pago in pagos:
        data.append({
            'id': pago.id,
            'fecha_pago': pago.fecha_pago.strftime('%d/%m/%Y %H:%M'),
            'monto': float(pago.monto),
            'metodo_pago': {
                'id': pago.metodo_pago.id,
                'nombre': pago.metodo_pago.nombre
            },
            'banco': {
                'id': pago.banco.id,
                'nombre': pago.banco.nombre
            } if pago.banco else None,
            'referencia_pago': pago.referencia_pago
        })
    
    return JsonResponse(data, safe=False)

@login_required
def metodo_pago_detalle(request, metodo_id):
    """API para obtener los detalles de un método de pago."""
    metodo = get_object_or_404(MetodoPago, pk=metodo_id)
    
    data = {
        'id': metodo.id,
        'nombre': metodo.nombre,
        'descripcion': metodo.descripcion,
        'requiere_banco': metodo.requiere_banco,
        'requiere_referencia': metodo.requiere_referencia
    }
    
    return JsonResponse(data)

@login_required
@permission_required('app_gimnasio.view_objetivo', raise_exception=True)
def objetivo_list(request):
    objetivos = Objetivo.objects.all().order_by('nombre')
    return render(request, 'app_gimnasio/objetivo_list.html', {'objetivos': objetivos})

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
