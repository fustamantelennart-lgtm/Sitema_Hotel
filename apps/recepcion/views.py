from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Hotel, Habitacion, TipoHabitacion
from apps.usuarios.decorators import rol_requerido


@login_required
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

    return render(request, 'recepcion/habitaciones.html', {
        'habitaciones': habitaciones,
        'q':            q,
        'hotel':        hotel,
    })


@login_required
@rol_requerido('admin', 'recepcionista')
def cambiar_estado(request, pk):
    habitacion = get_object_or_404(Habitacion, pk=pk)
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        if nuevo_estado in dict(Habitacion.ESTADO_CHOICES):
            habitacion.estado = nuevo_estado
            habitacion.save()
            messages.success(
                request,
                f'Habitación {habitacion.numero} → {habitacion.get_estado_display()}'
            )
        else:
            messages.error(request, 'Estado inválido.')
    return redirect('recepcion:habitaciones')


@login_required
@rol_requerido('admin')
def nueva_habitacion(request):
    hotel = Hotel.objects.first()
    tipos = TipoHabitacion.objects.filter(hotel=hotel)

    if request.method == 'POST':
        numero = request.POST.get('numero', '').strip()
        piso   = request.POST.get('piso', '')
        tipo_id = request.POST.get('tipo')
        obs    = request.POST.get('observaciones', '')

        if not numero or not piso or not tipo_id:
            messages.error(request, 'Completa todos los campos obligatorios.')
        elif Habitacion.objects.filter(hotel=hotel, numero=numero).exists():
            messages.error(request, f'Ya existe la habitación {numero}.')
        else:
            tipo = get_object_or_404(TipoHabitacion, pk=tipo_id)
            Habitacion.objects.create(
                hotel=hotel, tipo=tipo,
                numero=numero, piso=int(piso),
                observaciones=obs,
            )
            messages.success(request, f'Habitación {numero} creada correctamente.')
            return redirect('recepcion:habitaciones')

    return render(request, 'recepcion/nueva_habitacion.html', {
        'hotel': hotel,
        'tipos': tipos,
    })