from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from apps.recepcion.models import Hotel, TipoHabitacion, Habitacion
from apps.reservas.models import Huesped, Reserva, Tarifa
from .forms import ReservaPublicaForm


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
                    Q(fecha_entrada__lt=fs) &
                    Q(fecha_salida__gt=fe)
                ).count()

                habs_disponibles = tipo.habitaciones.filter(
                    estado='DISPONIBLE'
                ).count()

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

        user = request.user
        if user.is_authenticated and user.rol == 'cliente':
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
                initial['telefono']  = user.telefono

        form = ReservaPublicaForm(initial=initial)

    if request.method == 'POST':
        if form.is_valid():
            data = form.cleaned_data

            habitaciones_disponibles = Habitacion.objects.filter(
                hotel=hotel,
                tipo=data['tipo_habitacion'],
                estado__in=['DISPONIBLE', 'LIMPIEZA']
            )

            solapadas = Reserva.objects.filter(
                tipo_habitacion=data['tipo_habitacion'],
                estado__in=['PENDIENTE', 'CONFIRMADA', 'CHECKIN'],
            ).filter(
                Q(fecha_entrada__lt=data['fecha_salida']) &
                Q(fecha_salida__gt=data['fecha_entrada'])
            )

            if not habitaciones_disponibles.exists():
                messages.error(request, 'No hay habitaciones de ese tipo registradas.')
                return render(request, 'publica/reservar.html', {'form': form, 'hotel': hotel})

            if solapadas.count() >= habitaciones_disponibles.count():
                messages.error(request, 'No hay disponibilidad para las fechas seleccionadas.')
                return render(request, 'publica/reservar.html', {'form': form, 'hotel': hotel})

            huesped, _ = Huesped.objects.get_or_create(
                num_doc=data['num_doc'],
                defaults={
                    'tipo_doc':     data['tipo_doc'],
                    'nombres':      data['nombres'],
                    'apellidos':    data['apellidos'],
                    'email':        data['email'],
                    'telefono':     data['telefono'],
                    'nacionalidad': data['nacionalidad'],
                }
            )

            precio_noche = Tarifa.get_precio_vigente(
                data['tipo_habitacion'],
                data['fecha_entrada'],
                data['fecha_salida']
            )
            noches       = (data['fecha_salida'] - data['fecha_entrada']).days
            precio_total = precio_noche * noches

            reserva = Reserva.objects.create(
                hotel=hotel,
                huesped=huesped,
                tipo_habitacion=data['tipo_habitacion'],
                fecha_entrada=data['fecha_entrada'],
                fecha_salida=data['fecha_salida'],
                num_adultos=data['num_adultos'],
                num_ninos=data['num_ninos'],
                estado='PENDIENTE',
                precio_total=precio_total,
                origen='WEB',
                observaciones=data.get('observaciones', ''),
            )

            return redirect('publica:pago', pk=reserva.pk)

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
        metodo = request.POST.get('metodo_pago', 'tarjeta')

        if metodo == 'tarjeta':
            numero_tarjeta = request.POST.get('numero_tarjeta', '').replace(' ', '')
            cvv            = request.POST.get('cvv', '')
            nombre         = request.POST.get('nombre_tarjeta', '')
            expiracion     = request.POST.get('expiracion', '')

            errores = []
            if len(numero_tarjeta) != 16 or not numero_tarjeta.isdigit():
                errores.append('El número de tarjeta debe tener 16 dígitos.')
            if len(cvv) not in [3, 4] or not cvv.isdigit():
                errores.append('El CVV debe tener 3 o 4 dígitos.')
            if not nombre.strip():
                errores.append('Ingresa el nombre del titular.')
            if not expiracion:
                errores.append('Ingresa la fecha de vencimiento.')
            if numero_tarjeta == '4000000000000002':
                errores.append('Tarjeta rechazada. Intenta con otro método de pago.')

            if errores:
                for error in errores:
                    messages.error(request, error)
                return render(request, 'publica/pago.html', {'reserva': reserva})

        elif metodo == 'yape':
            num_op = request.POST.get('num_operacion_yape', '')
            if not num_op.strip():
                messages.error(request, 'Ingresa el número de operación de Yape.')
                return render(request, 'publica/pago.html', {'reserva': reserva})

        elif metodo == 'transferencia':
            num_op = request.POST.get('num_operacion_transferencia', '')
            if not num_op.strip():
                messages.error(request, 'Ingresa el número de operación de la transferencia.')
                return render(request, 'publica/pago.html', {'reserva': reserva})

        reserva.estado = 'CONFIRMADA'
        reserva.save()

        try:
            from django.core.mail import send_mail
            from django.conf import settings
            asunto  = f'¡Reserva confirmada y pago recibido! — {reserva.hotel.nombre}'
            mensaje = f"""Hola {reserva.huesped.nombres},

Tu pago fue procesado exitosamente y tu reserva está CONFIRMADA.

Código:     R-{reserva.pk}
Tipo:       {reserva.tipo_habitacion.nombre}
Entrada:    {reserva.fecha_entrada}
Salida:     {reserva.fecha_salida}
Noches:     {reserva.num_noches}
Total:      S/ {reserva.precio_total}

Preséntate en recepción el día de tu llegada con tu documento de identidad.
Check-in desde las 14:00 hrs.

¡Te esperamos!
{reserva.hotel.nombre}
{reserva.hotel.telefono}
"""
            send_mail(
                asunto, mensaje,
                settings.DEFAULT_FROM_EMAIL,
                [reserva.huesped.email],
                fail_silently=True,
            )
        except Exception:
            pass

        return redirect('publica:confirmacion', pk=reserva.pk)

    return redirect('publica:pago', pk=pk)


def confirmacion(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk, origen='WEB')
    return render(request, 'publica/confirmacion.html', {'reserva': reserva})


def detalle(request, pk):
    tipo          = get_object_or_404(TipoHabitacion, pk=pk)
    fecha_entrada = request.GET.get('fecha_entrada', '')
    fecha_salida  = request.GET.get('fecha_salida', '')
    return render(request, 'publica/detalle.html', {
        'tipo':          tipo,
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