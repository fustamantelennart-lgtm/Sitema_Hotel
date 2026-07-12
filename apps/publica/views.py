from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from apps.recepcion.models import Hotel, TipoHabitacion, Habitacion
from apps.reservas.models import Huesped, Reserva, Tarifa
from .forms import ReservaPublicaForm
from .services import ReservaPublicaService
from .exceptions import DisponibilidadAgotada, PagoInvalido, TarjetaRechazada


def inicio(request):
    from datetime import date
    hotel         = Hotel.objects.first()
    fecha_entrada = request.GET.get('fecha_entrada', '')
    fecha_salida  = request.GET.get('fecha_salida', '')
    num_adultos   = request.GET.get('num_adultos', 2)
    num_ninos     = request.GET.get('num_ninos', 0)
    noches        = None

    tipos_con_disponibilidad = []

    if fecha_entrada and fecha_salida:
        try:
            fe     = date.fromisoformat(fecha_entrada)
            fs     = date.fromisoformat(fecha_salida)
            noches = (fs - fe).days
        except Exception:
            noches = None

    for tipo in TipoHabitacion.objects.all():
        total_habs   = tipo.habitaciones.count()
        disponible   = None
        precio_total = None

        if fecha_entrada and fecha_salida and noches:
            try:
                fe = date.fromisoformat(fecha_entrada)
                fs = date.fromisoformat(fecha_salida)
                solapadas = Reserva.objects.filter(
                    tipo_habitacion=tipo,
                    estado__in=['PENDIENTE', 'CONFIRMADA', 'CHECKIN'],
                ).filter(
                    Q(fecha_entrada__lt=fs) & Q(fecha_salida__gt=fe)
                ).count()
                habs_disponibles = tipo.habitaciones.filter(estado='DISPONIBLE').count()
                disponible   = max(0, habs_disponibles - solapadas)
                precio_total = tipo.precio_base * noches
            except Exception:
                disponible   = None
                precio_total = None

        tipos_con_disponibilidad.append({
            'tipo':         tipo,
            'disponible':   disponible,
            'total':        total_habs,
            'precio_total': precio_total,
            'noches':       noches,
        })

    todos_agotados = False
    if fecha_entrada and fecha_salida:
        todos_agotados = all(
            item['disponible'] is not None and item['disponible'] == 0
            for item in tipos_con_disponibilidad
        )

    return render(request, 'publica/inicio.html', {
        'hotel':          hotel,
        'tipos':          tipos_con_disponibilidad,
        'fecha_entrada':  fecha_entrada,
        'fecha_salida':   fecha_salida,
        'num_adultos':    num_adultos,
        'num_ninos':      num_ninos,
        'noches':         noches,
        'todos_agotados': todos_agotados,
    })


def reservar(request):
    if not request.user.is_authenticated or request.user.rol != 'cliente':
        return redirect(f'/web/?login_required=1&next={request.get_full_path()}')

    hotel = Hotel.objects.first()
    form  = ReservaPublicaForm(request.POST or None)

    if request.method == 'GET':
        tipo_id       = request.GET.get('tipo')
        fecha_entrada = request.GET.get('fecha_entrada', '')
        fecha_salida  = request.GET.get('fecha_salida', '')
        num_adultos   = request.GET.get('num_adultos', 2)
        num_ninos     = request.GET.get('num_ninos', 0)

        initial = {}
        if tipo_id:       initial['tipo_habitacion'] = tipo_id
        if fecha_entrada: initial['fecha_entrada']   = fecha_entrada
        if fecha_salida:  initial['fecha_salida']    = fecha_salida
        if num_adultos:   initial['num_adultos']     = num_adultos
        if num_ninos:     initial['num_ninos']       = num_ninos

        user           = request.user
        huesped_previo = None
        try:
            huesped_previo = user.huesped
        except Exception:
            pass
        if not huesped_previo:
            huesped_previo = Huesped.objects.filter(email=user.email).first()

        if huesped_previo:
            initial['tipo_doc']     = huesped_previo.tipo_doc
            initial['num_doc']      = huesped_previo.num_doc
            initial['nombres']      = huesped_previo.nombres
            initial['apellidos']    = huesped_previo.apellidos
            initial['email']        = huesped_previo.email
            initial['telefono']     = huesped_previo.telefono
            initial['nacionalidad'] = huesped_previo.nacionalidad
        else:
            initial['nombres']   = user.first_name
            initial['apellidos'] = user.last_name
            initial['email']     = user.email
            initial['telefono']  = getattr(user, 'telefono', '')

        form = ReservaPublicaForm(initial=initial)

    if request.method == 'POST' and form.is_valid():
        try:
            reserva = ReservaPublicaService.crear_reserva_web(
                hotel   = hotel,
                data    = form.cleaned_data,
                usuario = request.user,
            )
            return redirect('publica:pago', pk=reserva.pk)
        except DisponibilidadAgotada as e:
            messages.error(request, str(e))

    return render(request, 'publica/reservar.html', {
        'form':  form,
        'hotel': hotel,
    })


def pago(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk, estado='PENDIENTE', origen='WEB')
    return render(request, 'publica/pago.html', {'reserva': reserva})


def procesar_pago(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk, estado='PENDIENTE', origen='WEB')

    if request.method == 'POST':
        try:
            metodo  = request.POST.get('metodo_pago', 'tarjeta')
            reserva = ReservaPublicaService.procesar_pago(
                reserva    = reserva,
                metodo     = metodo,
                datos_pago = request.POST,
            )
            return redirect('publica:confirmacion', pk=reserva.pk)
        except TarjetaRechazada as e:
            messages.error(request, str(e))
        except PagoInvalido as e:
            messages.error(request, str(e))

        return render(request, 'publica/pago.html', {'reserva': reserva})

    return redirect('publica:pago', pk=pk)


def confirmacion(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk, origen='WEB')
    return render(request, 'publica/confirmacion.html', {'reserva': reserva})


def detalle(request, pk):
    tipo          = get_object_or_404(TipoHabitacion, pk=pk)
    imagenes      = tipo.imagenes.all()
    fecha_entrada = request.GET.get('fecha_entrada', '')
    fecha_salida  = request.GET.get('fecha_salida', '')
    return render(request, 'publica/detalle.html', {
        'tipo':          tipo,
        'imagenes':      imagenes,
        'fecha_entrada': fecha_entrada,
        'fecha_salida':  fecha_salida,
    })


@require_GET
def consultar_dni(request):
    dni = request.GET.get('dni', '').strip()
    if not dni or len(dni) != 8 or not dni.isdigit():
        return JsonResponse({'error': 'DNI inválido.'}, status=400)
    from .dni import consultar_dni as _consultar
    data = _consultar(dni)
    if 'error' in data:
        return JsonResponse(data, status=404)
    return JsonResponse(data)