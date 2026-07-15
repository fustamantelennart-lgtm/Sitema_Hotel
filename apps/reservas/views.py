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
from .services import ReservaService, EstanciaService, FolioService
from .exceptions import (
    ReservaNoConfirmada, HabitacionNoDisponible, DeudasPendientesError,
    SolapamientoReservas, FechaPasadaError, CapacidadExcedida,
    FolioCerrado, EstanciaNoEncontrada
)


@login_required
@rol_requerido('admin', 'recepcionista')
def lista(request):
    hoy      = timezone.now().date()
    llegadas = Reserva.objects.filter(
        fecha_entrada=hoy, estado='CONFIRMADA'
    ).select_related('huesped', 'tipo_habitacion')
    en_casa  = Reserva.objects.filter(
        estado='CHECKIN'
    ).select_related('huesped', 'habitacion')
    salidas  = Reserva.objects.filter(
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
    from apps.recepcion.models import TipoHabitacion

    tipo_id = request.GET.get('tipo')
    initial = {'tipo_habitacion': tipo_id} if tipo_id else {}
    form    = ReservaPresencialForm(request.POST or None, initial=initial)

    if request.method == 'POST' and form.is_valid():
        huesped, _ = form.get_or_create_huesped()
        try:
            reserva = ReservaService.crear(
                data={
                    'huesped':         huesped,
                    'tipo_habitacion': form.cleaned_data['tipo_habitacion'],
                    'fecha_entrada':   form.cleaned_data['fecha_entrada'],
                    'fecha_salida':    form.cleaned_data['fecha_salida'],
                    'num_adultos':     form.cleaned_data['num_adultos'],
                    'num_ninos':       form.cleaned_data['num_ninos'],
                    'observaciones':   form.cleaned_data.get('observaciones', ''),
                    'estado':          'CONFIRMADA',
                    'origen':          'DIRECTO',
                },
                usuario=request.user,
            )
            accion = request.POST.get('accion', 'guardar')
            if accion == 'checkin':
                messages.success(request, f'Reserva #{reserva.pk} creada. Procede con el check-in.')
                return redirect('reservas:checkin', pk=reserva.pk)
            messages.success(request, f'Reserva #{reserva.pk} creada correctamente.')
            return redirect('reservas:lista')

        except FechaPasadaError as e:
            messages.error(request, str(e))
        except CapacidadExcedida as e:
            messages.error(request, str(e))
        except SolapamientoReservas as e:
            messages.error(request, str(e))

    precios = {str(t.pk): float(t.precio_base) for t in TipoHabitacion.objects.all()}
    return render(request, 'reservas/nueva.html', {
        'form':    form,
        'precios': json.dumps(precios),
    })


@login_required
@rol_requerido('admin', 'recepcionista')
def checkin(request, pk):
    reserva      = get_object_or_404(Reserva, pk=pk, estado='CONFIRMADA')
    habitaciones = Habitacion.objects.filter(
        hotel=reserva.hotel,
        tipo=reserva.tipo_habitacion,
        estado='DISPONIBLE'
    )
    if request.method == 'POST':
        hab_id = request.POST.get('habitacion')
        try:
            estancia = EstanciaService.checkin(
                reserva_id    = pk,
                habitacion_id = hab_id,
                usuario       = request.user,
            )
            messages.success(
                request,
                f'Check-in realizado. Habitación {estancia.habitacion.numero} asignada.'
            )
            return redirect('reservas:folio', pk=estancia.pk)
        except HabitacionNoDisponible as e:
            messages.error(request, str(e))
        except ReservaNoConfirmada as e:
            messages.error(request, str(e))

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
    if request.method == 'POST' and form.is_valid():
        try:
            cargo = FolioService.agregar_cargo(
                estancia_id = pk,
                concepto    = form.cleaned_data['concepto'],
                monto       = form.cleaned_data['monto'],
                tipo        = form.cleaned_data['tipo'],
                usuario     = request.user,
            )
            messages.success(request, f'Cargo "{cargo.concepto}" agregado.')
            return redirect('reservas:folio', pk=estancia.pk)
        except FolioCerrado as e:
            messages.error(request, str(e))

    return render(request, 'reservas/cargo.html', {
        'estancia': estancia,
        'form':     form,
    })


@login_required
@rol_requerido('admin', 'recepcionista')
def pagar_folio(request, pk):
    estancia = get_object_or_404(Estancia, pk=pk, estado='ACTIVA')
    if request.method == 'POST':
        try:
            metodo_pago       = request.POST.get('metodo_pago', 'EFECTIVO')
            folio             = estancia.folio
            folio.estado      = 'PAGADO'
            folio.fecha_pago  = timezone.now()
            folio.metodo_pago = metodo_pago
            folio.save()
            messages.success(request, f'Folio pagado con {metodo_pago}.')
        except FolioCerrado as e:
            messages.error(request, str(e))
    return redirect('reservas:folio', pk=estancia.pk)


@login_required
@rol_requerido('admin', 'recepcionista')
def checkout(request, pk):
    estancia = get_object_or_404(Estancia, pk=pk, estado='ACTIVA')
    if request.method == 'POST':
        try:
            estancia = EstanciaService.checkout(
                estancia_id = pk,
                usuario     = request.user,
            )
            messages.success(
                request,
                f'Checkout realizado. Habitación {estancia.habitacion.numero} en limpieza.'
            )
            return redirect('recepcion:dashboard')
        except DeudasPendientesError as e:
            messages.error(request, str(e))
            return redirect('reservas:folio', pk=pk)
        except EstanciaNoEncontrada as e:
            messages.error(request, str(e))

    cargos = estancia.cargos.all()
    return render(request, 'reservas/checkout.html', {
        'estancia':    estancia,
        'cargos':      cargos,
        'tiene_deuda': estancia.folio.tiene_deuda,
    })


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
    hoy = timezone.now().date()
    qs  = Reserva.objects.filter(
        estado='CONFIRMADA'
    ).select_related('huesped', 'tipo_habitacion').order_by('fecha_entrada')
    paginator = Paginator(qs, 15)
    page      = request.GET.get('page')
    llegadas  = paginator.get_page(page)
    return render(request, 'reservas/checkin_lista.html', {
        'llegadas': llegadas,
        'hoy':      hoy,
    })


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
    if request.method == 'POST':
        try:
            motivo   = request.POST.get('motivo', '')
            next_url = request.POST.get('next', 'reservas:lista')
            ReservaService.cancelar(pk, motivo, request.user)
            messages.success(request, f'Reserva R-{reserva.pk} cancelada correctamente.')
            return redirect(next_url)
        except ReservaNoConfirmada as e:
            messages.error(request, str(e))

    next_url = request.GET.get('next', 'reservas:lista')
    return render(request, 'reservas/cancelar.html', {
        'reserva': reserva,
        'next':    next_url,
    })


@login_required
@rol_requerido('admin', 'recepcionista')
def disponibilidad(request):
    from apps.recepcion.models import TipoHabitacion
    from datetime import date, timedelta
    from django.db.models import Q

    fecha_entrada = request.GET.get('fecha_entrada')
    fecha_salida  = request.GET.get('fecha_salida')
    tipo_id       = request.GET.get('tipo', '')
    resultados    = []
    tipos         = TipoHabitacion.objects.all()

    # Calendario — siempre mostrar 14 días desde hoy
    hoy        = date.today()
    dias       = [hoy + timedelta(days=i) for i in range(14)]
    habitaciones_cal = Habitacion.objects.select_related('tipo').order_by('piso', 'numero')
    pisos = habitaciones_cal.values_list('piso', flat=True).distinct().order_by('piso')
    # Para cada habitación obtener sus reservas en el período (directas o vía estancia activa)
    calendario = []
    for hab in habitaciones_cal:
        reservas_hab = list(Reserva.objects.filter(
            habitacion=hab,
            estado='CONFIRMADA',
            fecha_entrada__lte=dias[-1],
            fecha_salida__gte=dias[0],
        ).select_related('huesped'))

        estancias_hab = Estancia.objects.filter(
            habitacion=hab,
            estado='ACTIVA',
            reserva__fecha_entrada__lte=dias[-1],
            reserva__fecha_salida__gte=dias[0],
        ).select_related('reserva', 'reserva__huesped')

        for est in estancias_hab:
            reservas_hab.append(est.reserva)

        celdas = []
        for dia in dias:
            reserva_dia = None
            for r in reservas_hab:
                if r.fecha_entrada <= dia < r.fecha_salida:
                    reserva_dia = r
                    break
            celdas.append({
                'dia':     dia,
                'reserva': reserva_dia,
            })
        calendario.append({
            'habitacion': hab,
            'celdas':     celdas,
        })

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
        'calendario':    calendario,
        'dias':          dias,
        'pisos': pisos,
    })


@login_required
@rol_requerido('admin', 'recepcionista')
def solicitudes_web(request):
    solicitudes = Reserva.objects.filter(
        estado='CONFIRMADA', origen='WEB'
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
    en_casa  = Estancia.objects.filter(
        estado='ACTIVA'
    ).select_related('reserva__huesped', 'habitacion').order_by('fecha_checkin')
    return render(request, 'reservas/checkin_buscar.html', {
        'llegadas': llegadas,
        'en_casa':  en_casa,
    })