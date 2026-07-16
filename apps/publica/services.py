from django.db.models import Q
from apps.recepcion.models import Hotel, Habitacion, TipoHabitacion
from apps.reservas.models import Huesped, Reserva, Tarifa
from .exceptions import DisponibilidadAgotada, TarjetaRechazada, PagoInvalido


class ReservaPublicaService:

    @staticmethod
    def verificar_disponibilidad(hotel, tipo, fecha_entrada, fecha_salida):
        habitaciones = Habitacion.objects.filter(
            hotel=hotel,
            tipo=tipo,
            estado__in=['DISPONIBLE', 'LIMPIEZA']
        )

        if not habitaciones.exists():
            raise DisponibilidadAgotada(
                f'No hay habitaciones del tipo "{tipo.nombre}" registradas.'
            )

        solapadas = Reserva.objects.filter(
            tipo_habitacion=tipo,
            estado__in=['PENDIENTE', 'CONFIRMADA', 'CHECKIN'],
        ).filter(
            Q(fecha_entrada__lt=fecha_salida) &
            Q(fecha_salida__gt=fecha_entrada)
        )

        if solapadas.count() >= habitaciones.count():
            raise DisponibilidadAgotada(
                f'No hay disponibilidad para las fechas seleccionadas.'
            )

        return habitaciones

    @staticmethod
    def crear_reserva_web(hotel, data, usuario) -> Reserva:
        tipo = data['tipo_habitacion']
        fe   = data['fecha_entrada']
        fs   = data['fecha_salida']

        ReservaPublicaService.verificar_disponibilidad(hotel, tipo, fe, fs)

        huesped, _ = Huesped.objects.get_or_create(
            num_doc=data['num_doc'],
            defaults={
                'tipo_doc':      data['tipo_doc'],
                'nombres':       data['nombres'],
                'apellidos':     data['apellidos'],
                'email':         data['email'],
                'telefono':      data['telefono'],
                'nacionalidad':  data['nacionalidad'],
                'acepta_emails': data.get('acepta_emails', False),
            }
        )

        acepta_emails = data.get('acepta_emails', False)
        if huesped.usuario is None and usuario.is_authenticated:
            huesped.usuario       = usuario
            huesped.acepta_emails = acepta_emails
            huesped.save()
        elif acepta_emails:
            huesped.acepta_emails = True
            huesped.save(update_fields=['acepta_emails'])

        precio_noche = Tarifa.get_precio_vigente(tipo, fe, fs)
        noches       = (fs - fe).days
        precio_total = precio_noche * noches

        reserva = Reserva.objects.create(
            hotel            = hotel,
            huesped          = huesped,
            tipo_habitacion  = tipo,
            fecha_entrada    = fe,
            fecha_salida     = fs,
            num_adultos      = data['num_adultos'],
            num_ninos        = data['num_ninos'],
            estado           = 'PENDIENTE',
            precio_total     = precio_total,
            origen           = 'WEB',
            observaciones    = data.get('observaciones', ''),
            opcion_checkin   = data.get('opcion_checkin'),
            opcion_checkout  = data.get('opcion_checkout'),
        )
        return reserva

    @staticmethod
    def procesar_pago(reserva, metodo: str, datos_pago: dict) -> Reserva:
        if metodo == 'tarjeta':
            numero = datos_pago.get('numero_tarjeta', '').replace(' ', '')
            cvv    = datos_pago.get('cvv', '')
            nombre = datos_pago.get('nombre_tarjeta', '')
            exp    = datos_pago.get('expiracion', '')

            if len(numero) != 16 or not numero.isdigit():
                raise PagoInvalido('El número de tarjeta debe tener 16 dígitos.')
            if len(cvv) not in [3, 4] or not cvv.isdigit():
                raise PagoInvalido('El CVV debe tener 3 o 4 dígitos.')
            if not nombre.strip():
                raise PagoInvalido('Ingresa el nombre del titular.')
            if not exp:
                raise PagoInvalido('Ingresa la fecha de vencimiento.')
            if numero == '4000000000000002':
                raise TarjetaRechazada('Tarjeta rechazada. Intenta con otro método.')

        elif metodo == 'yape':
            if not datos_pago.get('num_operacion_yape', '').strip():
                raise PagoInvalido('Ingresa el número de operación de Yape.')

        elif metodo == 'transferencia':
            if not datos_pago.get('num_operacion_transferencia', '').strip():
                raise PagoInvalido('Ingresa el número de operación de la transferencia.')

        reserva.estado = 'CONFIRMADA'
        reserva.save()

        try:
            if reserva.huesped.acepta_emails and reserva.huesped.email:
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

        return reserva