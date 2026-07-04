from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import models
from django.core.paginator import Paginator
import json
from .models import Reserva, Estancia, CargoEstancia, Folio, Huesped, Tarifa
from apps.recepcion.models import Habitacion
from .forms import ReservaForm, CargoForm, HuespedForm
from apps.usuarios.decorators import rol_requerido


@login_required
@rol_requerido('admin', 'recepcionista')
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
    return render(request, 'reservas/lista.html', {
        'llegadas': llegadas,
        'en_casa':  en_casa,
        'salidas':  salidas,
        'hoy':      hoy,
    })


@login_required
@rol_requerido('admin', 'recepcionista')
def nueva(request):
    from .forms import ReservaPresencialForm
    from apps.recepcion.models import Hotel, TipoHabitacion

    tipo_id = request.GET.get('tipo')
    initial = {'tipo_habitacion': tipo_id} if tipo_id else {}
    form    = ReservaPresencialForm(request.POST or None, initial=initial)

    if request.method == 'POST' and form.is_valid():
        hotel                = Hotel.objects.first()
        huesped, created     = form.get_or_create_huesped()
        precio_noche         = Tarifa.get_precio_vigente(
            form.cleaned_data['tipo_habitacion'],
            form.cleaned_data['fecha_entrada'],
            form.cleaned_data['fecha_salida'],
        )
        noches       = (form.cleaned_data['fecha_salida'] - form.cleaned_data['fecha_entrada']).days
        precio_total = precio_noche * noches
        reserva = Reserva.objects.create(
            hotel           = hotel,
            huesped         = huesped,
            tipo_habitacion = form.cleaned_data['tipo_habitacion'],
            fecha_entrada   = form.cleaned_data['fecha_entrada'],
            fecha_salida    = form.cleaned_data['fecha_salida'],
            num_adultos     = form.cleaned_data['num_adultos'],
            num_ninos       = form.cleaned_data['num_ninos'],
            estado          = 'CONFIRMADA',
            precio_total    = precio_total,
            origen          = 'DIRECTO',
            observaciones   = form.cleaned_data.get('observaciones', ''),
            creado_por      = request.user,
        )
        accion = request.POST.get('accion', 'guardar')
        if accion == 'checkin':
            messages.success(request, f'Reserva #{reserva.pk} creada. Procede con el check-in.')
            return redirect('reservas:checkin', pk=reserva.pk)
        messages.success(request, f'Reserva #{reserva.pk} creada correctamente.')
        return redirect('reservas:lista')

    precios = {str(t.pk): float(t.precio_base) for t in TipoHabitacion.objects.all()}
    return render(request, 'reservas/nueva.html', {
        'form':    form,
        'precios': json.dumps(precios),
    })


@login_required
@rol_requerido('admin', 'recepcionista')
def checkin(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk, estado='CONFIRMADA')
    habitaciones = Habitacion.objects.filter(
        hotel=reserva.hotel,
        tipo=reserva.tipo_habitacion,
        estado='DISPONIBLE'
    )
    if request.method == 'POST':
        hab_id     = request.POST.get('habitacion')
        habitacion = get_object_or_404(Habitacion, pk=hab_id, estado='DISPONIBLE')
        estancia = Estancia.objects.create(
            reserva=reserva,
            habitacion=habitacion,
            atendido_por=request.user,
        )
        CargoEstancia.objects.create(
            estancia=estancia,
            concepto=f'Habitación {habitacion.numero} x {reserva.num_noches} noches',
            monto=reserva.precio_total,
            tipo='HABITACION',
            registrado_por=request.user,
        )
        folio = Folio.objects.create(estancia=estancia)
        folio.recalcular()
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
@rol_requerido('admin', 'recepcionista')
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
@rol_requerido('admin', 'recepcionista')
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
@rol_requerido('admin', 'recepcionista')
def pagar_folio(request, pk):
    estancia = get_object_or_404(Estancia, pk=pk, estado='ACTIVA')
    if request.method == 'POST':
        metodo_pago       = request.POST.get('metodo_pago', 'EFECTIVO')
        folio             = estancia.folio
        folio.estado      = 'PAGADO'
        folio.fecha_pago  = timezone.now()
        folio.metodo_pago = metodo_pago
        folio.save()
        messages.success(request, f'Folio pagado con {metodo_pago}.')
    return redirect('reservas:folio', pk=estancia.pk)


@login_required
@rol_requerido('admin', 'recepcionista')
def checkout(request, pk):
    estancia = get_object_or_404(Estancia, pk=pk, estado='ACTIVA')
    if estancia.tiene_deuda:
        messages.error(request, 'No se puede hacer checkout. El folio está pendiente de pago.')
        return redirect('reservas:folio', pk=estancia.pk)
    if request.method == 'POST':
        metodo_pago       = request.POST.get('metodo_pago', 'EFECTIVO')
        folio             = estancia.folio
        folio.estado      = 'PAGADO'
        folio.fecha_pago  = timezone.now()
        folio.metodo_pago = metodo_pago
        folio.save()
        estancia.estado         = 'FINALIZADA'
        estancia.fecha_checkout = timezone.now()
        estancia.save()
        reserva        = estancia.reserva
        reserva.estado = 'CHECKOUT'
        reserva.save()
        habitacion        = estancia.habitacion
        habitacion.estado = 'LIMPIEZA'
        habitacion.save()
        from apps.housekeeping.models import TareaLimpieza
        TareaLimpieza.objects.create(habitacion=habitacion, prioridad='ALTA')
        messages.success(request, f'Checkout realizado. Habitación {habitacion.numero} en limpieza.')
        return redirect('recepcion:dashboard')
    return render(request, 'reservas/checkout.html', {'estancia': estancia})


@login_required
@rol_requerido('admin', 'recepcionista')
def huespedes(request):
    q  = request.GET.get('q', '')
    qs = Huesped.objects.all().order_by('apellidos', 'nombres')
    if q:
        qs = qs.filter(
            models.Q(nombres__icontains=q)   |
            models.Q(apellidos__icontains=q) |
            models.Q(num_doc__icontains=q)
        )
    paginator = Paginator(qs, 15)
    page      = request.GET.get('page')
    huespedes = paginator.get_page(page)
    return render(request, 'reservas/huespedes.html', {
        'huespedes': huespedes,
        'q':         q,
    })


@login_required
@rol_requerido('admin', 'recepcionista')
def checkin_lista(request):
    qs = Reserva.objects.filter(
        estado='CONFIRMADA'
    ).select_related('huesped', 'tipo_habitacion').order_by('fecha_entrada')
    paginator = Paginator(qs, 15)
    page      = request.GET.get('page')
    llegadas  = paginator.get_page(page)
    return render(request, 'reservas/checkin_lista.html', {'llegadas': llegadas})


@login_required
@rol_requerido('admin', 'recepcionista')
def checkout_lista(request):
    qs = Estancia.objects.filter(
        estado='ACTIVA'
    ).select_related('reserva__huesped', 'habitacion').order_by('fecha_checkin')
    paginator = Paginator(qs, 15)
    page      = request.GET.get('page')
    en_casa   = paginator.get_page(page)
    return render(request, 'reservas/checkout_lista.html', {'en_casa': en_casa})


@login_required
@rol_requerido('admin', 'recepcionista')
def cancelar(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk)
    if reserva.estado not in ('PENDIENTE', 'CONFIRMADA'):
        messages.error(request, 'Solo se pueden cancelar reservas pendientes o confirmadas.')
        return redirect('reservas:lista')
    if request.method == 'POST':
        motivo          = request.POST.get('motivo', '')
        reserva.estado  = 'CANCELADA'
        reserva.observaciones += f'\nCancelada por {request.user}: {motivo}'
        reserva.save()
        messages.success(request, f'Reserva R-{reserva.pk} cancelada correctamente.')
        return redirect('reservas:lista')
    return render(request, 'reservas/cancelar.html', {'reserva': reserva})


@login_required
@rol_requerido('admin', 'recepcionista')
def disponibilidad(request):
    from apps.recepcion.models import TipoHabitacion
    from datetime import date
    from django.db.models import Q
    fecha_entrada = request.GET.get('fecha_entrada')
    fecha_salida  = request.GET.get('fecha_salida')
    tipo_id       = request.GET.get('tipo', '')
    resultados    = []
    tipos         = TipoHabitacion.objects.all()

    if fecha_entrada and fecha_salida:
        fe = date.fromisoformat(fecha_entrada)
        fs = date.fromisoformat(fecha_salida)
        habitaciones = Habitacion.objects.select_related('tipo').filter(
            estado__in=['DISPONIBLE', 'LIMPIEZA']
        )
        if tipo_id:
            habitaciones = habitaciones.filter(tipo_id=tipo_id)
        for hab in habitaciones:
            solapada = Reserva.objects.filter(
                habitacion=hab,
                estado__in=['PENDIENTE', 'CONFIRMADA', 'CHECKIN'],
            ).filter(
                Q(fecha_entrada__lt=fs) & Q(fecha_salida__gt=fe)
            ).exists()
            if not solapada:
                resultados.append(hab)

    return render(request, 'reservas/disponibilidad.html', {
        'resultados':    resultados,
        'tipos':         tipos,
        'fecha_entrada': fecha_entrada or '',
        'fecha_salida':  fecha_salida or '',
        'tipo_id':       tipo_id,
        'buscado':       bool(fecha_entrada and fecha_salida),
    })


@login_required
@rol_requerido('admin', 'recepcionista')
def solicitudes_web(request):
    solicitudes = Reserva.objects.filter(
        estado='PENDIENTE', origen='WEB'
    ).select_related('huesped', 'tipo_habitacion').order_by('fecha_entrada')
    return render(request, 'reservas/solicitudes_web.html', {'solicitudes': solicitudes})


@login_required
@rol_requerido('admin', 'recepcionista')
def confirmar_solicitud(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk, estado='PENDIENTE', origen='WEB')
    if request.method == 'POST':
        reserva.estado     = 'CONFIRMADA'
        reserva.creado_por = request.user
        reserva.save()
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            send_mail(
                f'¡Reserva confirmada! — {reserva.hotel.nombre}',
                f'Hola {reserva.huesped.nombres}, tu reserva R-{reserva.pk} fue CONFIRMADA.',
                settings.DEFAULT_FROM_EMAIL,
                [reserva.huesped.email],
                fail_silently=True,
            )
        except Exception:
            pass
        messages.success(request, f'Reserva R-{reserva.pk} confirmada.')
    return redirect('reservas:solicitudes_web')


@login_required
@rol_requerido('admin', 'recepcionista')
def rechazar_solicitud(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk, estado='PENDIENTE', origen='WEB')
    if request.method == 'POST':
        reserva.estado = 'CANCELADA'
        reserva.save()
        messages.success(request, f'Reserva R-{reserva.pk} rechazada.')
    return redirect('reservas:solicitudes_web')


@login_required
@rol_requerido('admin', 'recepcionista')
def huesped_detalle(request, pk):
    huesped  = get_object_or_404(Huesped, pk=pk)
    reservas = Reserva.objects.filter(
        huesped=huesped
    ).select_related('tipo_habitacion', 'hotel').order_by('-fecha_entrada')
    return render(request, 'reservas/huesped_detalle.html', {
        'huesped':  huesped,
        'reservas': reservas,
    })


@login_required
@rol_requerido('admin', 'recepcionista')
def checkin_buscar(request):
    llegadas = Reserva.objects.filter(
        estado='CONFIRMADA'
    ).select_related('huesped', 'tipo_habitacion').order_by('fecha_entrada')
    en_casa = Estancia.objects.filter(
        estado='ACTIVA'
    ).select_related('reserva__huesped', 'habitacion').order_by('fecha_checkin')
    return render(request, 'reservas/checkin_buscar.html', {
        'llegadas': llegadas,
        'en_casa':  en_casa,
    })