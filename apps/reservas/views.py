from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Reserva, Estancia, CargoEstancia, Folio, Huesped, Tarifa
from apps.recepcion.models import Habitacion
from .forms import ReservaForm, CargoForm


@login_required
def lista(request):
    hoy = timezone.now().date()
    llegadas = Reserva.objects.filter(
        fecha_entrada=hoy, estado='CONFIRMADA'
    ).select_related('huesped', 'tipo_habitacion')
    en_casa = Reserva.objects.filter(
        estado='CHECKIN'
    ).select_related('huesped', 'habitacion')
    salidas = Reserva.objects.filter(
        fecha_salida=hoy, estado='CHECKIN'
    ).select_related('huesped', 'habitacion')
    context = {
        'llegadas': llegadas,
        'en_casa':  en_casa,
        'salidas':  salidas,
        'hoy':      hoy,
    }
    return render(request, 'reservas/lista.html', context)


@login_required
def nueva(request):
    form = ReservaForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            reserva = form.save(commit=False)
            reserva.creado_por = request.user
            reserva.calcular_precio()
            reserva.save()
            messages.success(request, f'Reserva #{reserva.pk} creada correctamente.')
            return redirect('reservas:lista')
    return render(request, 'reservas/nueva.html', {'form': form})


@login_required
def checkin(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk, estado='CONFIRMADA')

    # REGLA: solo habitaciones DISPONIBLES del mismo tipo
    habitaciones = Habitacion.objects.filter(
        hotel=reserva.hotel,
        tipo=reserva.tipo_habitacion,
        estado='DISPONIBLE'
    )

    if request.method == 'POST':
        hab_id     = request.POST.get('habitacion')
        habitacion = get_object_or_404(Habitacion, pk=hab_id, estado='DISPONIBLE')

        # Crear estancia
        estancia = Estancia.objects.create(
            reserva=reserva,
            habitacion=habitacion,
            atendido_por=request.user,
        )
        # Cargo inicial por habitación
        CargoEstancia.objects.create(
            estancia=estancia,
            concepto=f'Habitación {habitacion.numero} x {reserva.num_noches} noches',
            monto=reserva.precio_total,
            tipo='HABITACION',
            registrado_por=request.user,
        )
        # Crear y calcular folio
        folio = Folio.objects.create(estancia=estancia)
        folio.recalcular()

        # Cambiar estados
        habitacion.estado  = 'OCUPADA'
        habitacion.save()
        reserva.estado     = 'CHECKIN'
        reserva.habitacion = habitacion
        reserva.save()

        messages.success(request, f'Check-in realizado. Habitación {habitacion.numero} asignada.')
        return redirect('reservas:folio', pk=estancia.pk)

    return render(request, 'reservas/checkin.html', {
        'reserva':      reserva,
        'habitaciones': habitaciones,
    })


@login_required
def folio(request, pk):
    estancia = get_object_or_404(Estancia, pk=pk)
    folio    = get_object_or_404(Folio, estancia=estancia)
    cargos   = estancia.cargos.all()
    return render(request, 'reservas/folio.html', {
        'estancia': estancia,
        'folio':    folio,
        'cargos':   cargos,
    })


@login_required
def agregar_cargo(request, pk):
    estancia = get_object_or_404(Estancia, pk=pk, estado='ACTIVA')
    form     = CargoForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            cargo                = form.save(commit=False)
            cargo.estancia       = estancia
            cargo.registrado_por = request.user
            cargo.save()
            estancia.folio.recalcular()
            messages.success(request, f'Cargo "{cargo.concepto}" agregado.')
            return redirect('reservas:folio', pk=estancia.pk)
    return render(request, 'reservas/cargo.html', {
        'estancia': estancia,
        'form':     form,
    })


@login_required
def checkout(request, pk):
    estancia = get_object_or_404(Estancia, pk=pk, estado='ACTIVA')

    # REGLA CRÍTICA: no checkout con deuda
    if estancia.tiene_deuda:
        messages.error(request, 'No se puede hacer checkout. El folio está pendiente de pago.')
        return redirect('reservas:folio', pk=estancia.pk)

    if request.method == 'POST':
        metodo_pago = request.POST.get('metodo_pago', 'EFECTIVO')

        # Cerrar folio
        folio             = estancia.folio
        folio.estado      = 'PAGADO'
        folio.fecha_pago  = timezone.now()
        folio.metodo_pago = metodo_pago
        folio.save()

        # Cerrar estancia
        estancia.estado         = 'FINALIZADA'
        estancia.fecha_checkout = timezone.now()
        estancia.save()

        # Cambiar estado reserva
        reserva        = estancia.reserva
        reserva.estado = 'CHECKOUT'
        reserva.save()

        # REGLA CRÍTICA: habitación pasa a LIMPIEZA
        habitacion        = estancia.habitacion
        habitacion.estado = 'LIMPIEZA'
        habitacion.save()

        # Crear tarea de limpieza automáticamente
        from apps.housekeeping.models import TareaLimpieza
        TareaLimpieza.objects.create(
            habitacion=habitacion,
            prioridad='ALTA',
        )

        messages.success(request, f'Checkout realizado. Habitación {habitacion.numero} en limpieza.')
        return redirect('recepcion:dashboard')

    return render(request, 'reservas/checkout.html', {'estancia': estancia})


@login_required
def huespedes(request):
    lista_huespedes = Huesped.objects.all().order_by('apellidos', 'nombres')
    return render(request, 'reservas/huespedes.html', {'huespedes': lista_huespedes})


@login_required
def checkin_buscar(request):
    llegadas = Reserva.objects.filter(
        estado='CONFIRMADA'
    ).select_related('huesped', 'tipo_habitacion').order_by('fecha_entrada')
    return render(request, 'reservas/checkin_buscar.html', {'llegadas': llegadas})