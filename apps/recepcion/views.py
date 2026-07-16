from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Hotel, Habitacion, TipoHabitacion
from apps.usuarios.decorators import rol_requerido
from .services import HabitacionService
from .exceptions import (
    HabitacionNoEncontrada, EstadoInvalido,
    HabitacionDuplicada, CambioEstadoNoPermitido
)


@login_required
@rol_requerido('admin', 'recepcionista')
def dashboard(request):
    hotel        = Hotel.objects.first()
    habitaciones = Habitacion.objects.filter(
        hotel=hotel
    ).select_related('tipo').order_by('piso', 'numero')
    pisos = {}
    for hab in habitaciones:
        pisos.setdefault(hab.piso, []).append(hab)
    context = {
        'hotel':       hotel,
        'pisos':       pisos,
        'disponibles': habitaciones.filter(estado='DISPONIBLE').count(),
        'ocupadas':    habitaciones.filter(estado='OCUPADA').count(),
        'limpieza':    habitaciones.filter(estado='LIMPIEZA').count(),
        'mant':        habitaciones.filter(estado='MANTENIMIENTO').count(),
        'total':       habitaciones.count(),
    }
    return render(request, 'recepcion/dashboard.html', context)


@login_required
@rol_requerido('admin', 'recepcionista')
def habitaciones(request):
    hotel        = Hotel.objects.first()
    habitaciones = Habitacion.objects.filter(
        hotel=hotel
    ).select_related('tipo').order_by('piso', 'numero')
    q = request.GET.get('q', '')
    if q:
        habitaciones = habitaciones.filter(numero__icontains=q)
    pisos = {}
    for hab in habitaciones:
        pisos.setdefault(hab.piso, []).append(hab)
    return render(request, 'recepcion/habitaciones.html', {
        'habitaciones': habitaciones,
        'pisos':        pisos,
        'q':            q,
        'hotel':        hotel,
    })


@login_required
@rol_requerido('admin', 'recepcionista')
def cambiar_estado(request, pk):
    if request.method == 'POST':
        try:
            nuevo_estado = request.POST.get('estado')
            habitacion   = HabitacionService.cambiar_estado(pk, nuevo_estado, request.user)
            messages.success(
                request,
                f'Habitación {habitacion.numero} → {habitacion.get_estado_display()}'
            )
        except CambioEstadoNoPermitido as e:
            messages.error(request, str(e))
        except EstadoInvalido as e:
            messages.error(request, str(e))
        except HabitacionNoEncontrada as e:
            messages.error(request, str(e))
    return redirect('recepcion:habitaciones')


@login_required
@rol_requerido('admin')
def nueva_habitacion(request):
    hotel = Hotel.objects.first()
    tipos = TipoHabitacion.objects.filter(hotel=hotel)

    if request.method == 'POST':
        try:
            habitacion = HabitacionService.crear_habitacion(
                numero        = request.POST.get('numero', '').strip(),
                piso          = request.POST.get('piso', ''),
                tipo_id       = request.POST.get('tipo'),
                observaciones = request.POST.get('observaciones', ''),
                hotel         = hotel,
            )
            messages.success(request, f'Habitación {habitacion.numero} creada correctamente.')
            return redirect('recepcion:habitaciones')
        except HabitacionDuplicada as e:
            messages.error(request, str(e))
        except EstadoInvalido as e:
            messages.error(request, str(e))
        except HabitacionNoEncontrada as e:
            messages.error(request, str(e))

    return render(request, 'recepcion/nueva_habitacion.html', {
        'hotel': hotel,
        'tipos': tipos,
    })