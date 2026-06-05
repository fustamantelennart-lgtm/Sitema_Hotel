from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Hotel, Habitacion


@login_required
def dashboard(request):
    hotel = Hotel.objects.first()
    habitaciones = Habitacion.objects.filter(
        hotel=hotel
    ).select_related('tipo').order_by('piso', 'numero')

    # Agrupar por piso para el mapa
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