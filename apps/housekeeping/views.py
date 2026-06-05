from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import TareaLimpieza


@login_required
def panel(request):
    tareas = TareaLimpieza.objects.filter(
        estado__in=['PENDIENTE', 'EN_PROCESO']
    ).select_related('habitacion', 'habitacion__tipo', 'asignada_a').order_by(
        'habitacion__piso', 'habitacion__numero'
    )

    pendientes  = tareas.filter(estado='PENDIENTE').count()
    en_proceso  = tareas.filter(estado='EN_PROCESO').count()
    listas_hoy  = TareaLimpieza.objects.filter(
        estado='LISTA',
        fecha_completada__date=timezone.now().date()
    ).count()

    return render(request, 'housekeeping/panel.html', {
        'tareas':     tareas,
        'pendientes': pendientes,
        'en_proceso': en_proceso,
        'listas_hoy': listas_hoy,
    })


@login_required
def iniciar(request, pk):
    tarea = get_object_or_404(TareaLimpieza, pk=pk)
    if request.method == 'POST':
        tarea.estado     = 'EN_PROCESO'
        tarea.asignada_a = request.user
        tarea.save()
        messages.success(request, f'Tarea Hab. {tarea.habitacion.numero} en proceso.')
    return redirect('housekeeping:panel')


@login_required
def completar(request, pk):
    tarea = get_object_or_404(TareaLimpieza, pk=pk)
    if request.method == 'POST':
        tarea.marcar_lista()
        messages.success(
            request,
            f'Habitación {tarea.habitacion.numero} lista — ahora está Disponible.'
        )
    return redirect('housekeeping:panel')