from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import TareaLimpieza, IncidenteHabitacion
from .services import HousekeepingService
from .exceptions import TareaYaIniciada, TareaYaCompletada
from apps.usuarios.decorators import rol_requerido


@login_required
@rol_requerido('admin', 'housekeeping')
def panel(request):
    tareas = TareaLimpieza.objects.filter(
        estado__in=['PENDIENTE', 'EN_PROCESO']
    ).select_related('habitacion', 'habitacion__tipo', 'asignada_a').order_by(
        '-prioridad', 'habitacion__piso', 'habitacion__numero'
    )
    pendientes = tareas.filter(estado='PENDIENTE').count()
    en_proceso = tareas.filter(estado='EN_PROCESO').count()
    listas_hoy = TareaLimpieza.objects.filter(
        estado='LISTA',
        fecha_completada__date=timezone.now().date()
    ).count()

    from apps.usuarios.models import Usuario
    empleados = Usuario.objects.filter(rol='housekeeping', is_active=True)

    return render(request, 'housekeeping/panel.html', {
        'tareas':     tareas,
        'pendientes': pendientes,
        'en_proceso': en_proceso,
        'listas_hoy': listas_hoy,
        'empleados':  empleados,
    })


@login_required
@rol_requerido('admin', 'housekeeping')
def iniciar(request, pk):
    if request.method == 'POST':
        try:
            tarea = HousekeepingService.iniciar_tarea(pk, request.user)
            messages.success(request, f'Tarea Hab. {tarea.habitacion.numero} en proceso.')
        except TareaYaIniciada as e:
            messages.error(request, str(e))
        except TareaYaCompletada as e:
            messages.error(request, str(e))
    return redirect('housekeeping:panel')


@login_required
@rol_requerido('admin', 'housekeeping')
def completar(request, pk):
    if request.method == 'POST':
        try:
            tarea = HousekeepingService.completar_tarea(pk)
            messages.success(
                request,
                f'Habitación {tarea.habitacion.numero} lista — ahora está Disponible.'
            )
        except TareaYaCompletada as e:
            messages.error(request, str(e))
    return redirect('housekeeping:panel')


@login_required
@rol_requerido('admin', 'housekeeping')
def asignar(request, pk):
    if request.method == 'POST':
        try:
            tarea = HousekeepingService.asignar_tarea(
                tarea_id    = pk,
                empleado_id = request.POST.get('empleado'),
                prioridad   = request.POST.get('prioridad'),
            )
            messages.success(request, f'Tarea Hab. {tarea.habitacion.numero} actualizada.')
        except Exception as e:
            messages.error(request, str(e))
    return redirect('housekeeping:panel')


@login_required
@rol_requerido('admin', 'housekeeping')
def historial(request):
    from django.core.paginator import Paginator

    tareas = TareaLimpieza.objects.filter(
        estado='LISTA'
    ).select_related('habitacion', 'habitacion__tipo', 'asignada_a').order_by(
        '-fecha_completada'
    )
    fecha = request.GET.get('fecha')
    if fecha:
        from datetime import date
        tareas = tareas.filter(fecha_completada__date=date.fromisoformat(fecha))

    paginator   = Paginator(tareas, 15)
    numero_pagina = request.GET.get('page')
    pagina      = paginator.get_page(numero_pagina)

    return render(request, 'housekeeping/historial.html', {
        'tareas': pagina,
        'pagina': pagina,
        'fecha':  fecha or '',
    })


@login_required
@rol_requerido('admin', 'housekeeping')
def incidentes(request):
    qs = IncidenteHabitacion.objects.select_related(
        'habitacion', 'reportado_por'
    ).order_by('-fecha')

    resuelto = request.GET.get('resuelto', '')
    if resuelto == '1':
        qs = qs.filter(resuelto=True)
    elif resuelto == '0':
        qs = qs.filter(resuelto=False)

    pendientes = IncidenteHabitacion.objects.filter(resuelto=False).count()

    return render(request, 'housekeeping/incidentes.html', {
        'incidentes': qs,
        'pendientes': pendientes,
        'resuelto':   resuelto,
    })


@login_required
@rol_requerido('admin', 'housekeeping')
def reportar_incidente(request):
    tarea_id = request.GET.get('tarea') or request.POST.get('tarea')

    if request.method == 'POST':
        try:
            incidente = HousekeepingService.reportar_incidente(
                habitacion_id = request.POST.get('habitacion'),
                tipo          = request.POST.get('tipo'),
                descripcion   = request.POST.get('descripcion'),
                monto_cobrar  = request.POST.get('monto_cobrar') or None,
                usuario       = request.user,
                tarea_id      = tarea_id,
            )
            messages.success(request, f'Consumo/incidente registrado en Hab. {incidente.habitacion.numero}.')
            if tarea_id:
                return redirect(f"{reverse('housekeeping:reportar_incidente')}?habitacion={incidente.habitacion.pk}&tarea={tarea_id}")
            return redirect('housekeeping:incidentes')
        except Exception as e:
            messages.error(request, str(e))

    from apps.recepcion.models import Habitacion
    habitaciones = Habitacion.objects.filter(
        estado__in=['OCUPADA', 'LIMPIEZA']
    ).order_by('piso', 'numero')
    habitacion_preseleccionada = request.GET.get('habitacion')
    return render(request, 'housekeeping/reportar_incidente.html', {
        'habitaciones': habitaciones,
        'habitacion_preseleccionada': habitacion_preseleccionada,
        'tarea_id': tarea_id,
    })


@login_required
@rol_requerido('admin', 'housekeeping')
def resolver_incidente(request, pk):
    if request.method == 'POST':
        try:
            incidente = HousekeepingService.resolver_incidente(pk)
            messages.success(request, f'Incidente en Hab. {incidente.habitacion.numero} resuelto.')
        except Exception as e:
            messages.error(request, str(e))
    return redirect('housekeeping:incidentes')