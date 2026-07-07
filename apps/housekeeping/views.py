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
        '-prioridad', 'habitacion__piso', 'habitacion__numero'
    )
    pendientes = tareas.filter(estado='PENDIENTE').count()
    en_proceso = tareas.filter(estado='EN_PROCESO').count()
    listas_hoy = TareaLimpieza.objects.filter(
        estado='LISTA',
        fecha_completada__date=timezone.now().date()
    ).count()

    # Usuarios housekeeping para asignación
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


@login_required
def asignar(request, pk):
    tarea = get_object_or_404(TareaLimpieza, pk=pk)
    if request.method == 'POST':
        empleado_id = request.POST.get('empleado')
        prioridad   = request.POST.get('prioridad')
        if empleado_id:
            from apps.usuarios.models import Usuario
            tarea.asignada_a = get_object_or_404(Usuario, pk=empleado_id)
        if prioridad:
            tarea.prioridad = prioridad
        tarea.save()
        messages.success(request, f'Tarea Hab. {tarea.habitacion.numero} actualizada.')
    return redirect('housekeeping:panel')


@login_required
def historial(request):
    tareas = TareaLimpieza.objects.filter(
        estado='LISTA'
    ).select_related('habitacion', 'habitacion__tipo', 'asignada_a').order_by(
        '-fecha_completada'
    )

    # Filtro por fecha
    fecha = request.GET.get('fecha')
    if fecha:
        from datetime import date
        tareas = tareas.filter(fecha_completada__date=date.fromisoformat(fecha))

    return render(request, 'housekeeping/historial.html', {
        'tareas': tareas,
        'fecha':  fecha or '',
    })
@login_required
def incidentes(request):
    from .models import IncidenteHabitacion
    qs = IncidenteHabitacion.objects.select_related(
        'habitacion', 'reportado_por'
    ).order_by('-fecha')

    # Filtro
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
def reportar_incidente(request):
    from .models import IncidenteHabitacion
    from apps.recepcion.models import Habitacion

    if request.method == 'POST':
        hab_id      = request.POST.get('habitacion')
        tipo        = request.POST.get('tipo')
        descripcion = request.POST.get('descripcion')
        monto       = request.POST.get('monto_cobrar') or None

        habitacion = get_object_or_404(Habitacion, pk=hab_id)
        IncidenteHabitacion.objects.create(
            habitacion    = habitacion,
            tipo          = tipo,
            descripcion   = descripcion,
            monto_cobrar  = monto,
            reportado_por = request.user,
        )
        messages.success(request, f'Incidente reportado en Hab. {habitacion.numero}.')
        return redirect('housekeeping:incidentes')

    from apps.recepcion.models import Habitacion
    habitaciones = Habitacion.objects.filter(
        estado__in=['OCUPADA', 'LIMPIEZA']
    ).order_by('piso', 'numero')
    return render(request, 'housekeeping/reportar_incidente.html', {
        'habitaciones': habitaciones,
    })


@login_required
def resolver_incidente(request, pk):
    from .models import IncidenteHabitacion
    incidente = get_object_or_404(IncidenteHabitacion, pk=pk)
    if request.method == 'POST':
        incidente.resuelto = True
        incidente.save()
        messages.success(request, f'Incidente en Hab. {incidente.habitacion.numero} resuelto.')
    return redirect('housekeeping:incidentes')