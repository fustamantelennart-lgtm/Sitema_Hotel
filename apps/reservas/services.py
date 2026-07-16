from django.db import transaction
from django.utils import timezone
from .models import Reserva, Estancia, Folio, CargoEstancia, Huesped, Tarifa
from .exceptions import (
    ReservaNoConfirmada, HabitacionNoDisponible, DeudasPendientesError,
    SolapamientoReservas, FechaPasadaError, CapacidadExcedida,
    FolioCerrado, EstanciaNoEncontrada
)


class ReservaService:

    @staticmethod
    @transaction.atomic
    def crear(data: dict, usuario) -> Reserva:
        from django.db.models import Q
        from apps.recepcion.models import Hotel, Habitacion

        fe          = data['fecha_entrada']
        fs          = data['fecha_salida']
        tipo        = data['tipo_habitacion']
        num_adultos = data.get('num_adultos', 1)
        num_ninos   = data.get('num_ninos', 0)
        hoy         = timezone.now().date()

        # 1. Fecha no puede ser en el pasado
        if fe < hoy:
            raise FechaPasadaError('La fecha de entrada no puede ser en el pasado.')

        # 2. Fecha salida posterior a entrada
        if fs <= fe:
            raise FechaPasadaError('La fecha de salida debe ser posterior a la entrada.')

        # 3. Capacidad máxima
        total = num_adultos + num_ninos
        if total > tipo.capacidad:
            raise CapacidadExcedida(
                f'El tipo "{tipo.nombre}" tiene capacidad máxima de '
                f'{tipo.capacidad} persona(s). Ingresaste {total}.'
            )

        # 4. Solapamiento
        from apps.recepcion.models import Habitacion
        habitaciones = Habitacion.objects.filter(tipo=tipo, estado='DISPONIBLE')
        libres = 0
        for hab in habitaciones:
            solapada = Reserva.objects.filter(
                habitacion=hab,
                estado__in=['PENDIENTE', 'CONFIRMADA', 'CHECKIN'],
            ).filter(
                Q(fecha_entrada__lt=fs) & Q(fecha_salida__gt=fe)
            ).exists()
            if not solapada:
                libres += 1

        if libres == 0:
            raise SolapamientoReservas(
                f'No hay habitaciones disponibles del tipo "{tipo.nombre}" '
                f'para las fechas {fe.strftime("%d/%m/%Y")} → {fs.strftime("%d/%m/%Y")}.'
            )

        # 5. Calcular precio
        hotel        = Hotel.objects.first()
        precio_noche = Tarifa.get_precio_vigente(tipo, fe, fs)
        noches       = (fs - fe).days
        precio_total = precio_noche * noches

        # 6. Crear reserva
        reserva = Reserva.objects.create(
            hotel           = hotel,
            huesped         = data['huesped'],
            tipo_habitacion = tipo,
            fecha_entrada   = fe,
            fecha_salida    = fs,
            num_adultos     = num_adultos,
            num_ninos       = num_ninos,
            estado          = data.get('estado', 'CONFIRMADA'),
            precio_total    = precio_total,
            origen          = data.get('origen', 'DIRECTO'),
            observaciones   = data.get('observaciones', ''),
            creado_por      = usuario,
        )
        return reserva

    @staticmethod
    def cancelar(reserva_id: int, motivo: str, usuario) -> Reserva:
        reserva = Reserva.objects.get(pk=reserva_id)
        if reserva.estado not in ('PENDIENTE', 'CONFIRMADA'):
            raise ReservaNoConfirmada('Solo se pueden cancelar reservas pendientes o confirmadas.')
        reserva.estado        = 'CANCELADA'
        reserva.observaciones += f'\nCancelada por {usuario}: {motivo}'
        reserva.save()
        return reserva


class EstanciaService:

    @staticmethod
    @transaction.atomic
    def checkin(reserva_id: int, habitacion_id: int, usuario) -> Estancia:
        from apps.recepcion.models import Habitacion

        reserva = Reserva.objects.select_related(
            'huesped', 'tipo_habitacion'
        ).get(pk=reserva_id)

        if reserva.estado != 'CONFIRMADA':
            raise ReservaNoConfirmada(
                f'La reserva R-{reserva_id} no está confirmada.'
            )

        habitacion = Habitacion.objects.get(pk=habitacion_id)

        if habitacion.estado in ['MANTENIMIENTO', 'LIMPIEZA', 'OCUPADA']:
            raise HabitacionNoDisponible(
                f'Habitación {habitacion.numero} no está disponible '
                f'(estado: {habitacion.get_estado_display()}).'
            )

        # Crear estancia
        estancia = Estancia.objects.create(
            reserva      = reserva,
            habitacion   = habitacion,
            atendido_por = usuario,
        )

# Cargo base de habitación
        noches = reserva.num_noches
        CargoEstancia.objects.create(
            estancia       = estancia,
            concepto       = f'Habitación {habitacion.numero} — {noches} noche(s){"  ✓ Pagado en reserva web" if reserva.origen == "WEB" else ""}',
            monto          = reserva.precio_total if reserva.origen != 'WEB' else 0,
            tipo           = 'HABITACION',
            registrado_por = usuario,
        )
        # Cargos extra por opciones de check-in/out
        if reserva.opcion_checkin and reserva.opcion_checkin.cargo_extra > 0:
            CargoEstancia.objects.create(
                estancia       = estancia,
                concepto       = f'Early check-in — {reserva.opcion_checkin.nombre}',
                monto          = reserva.opcion_checkin.cargo_extra,
                tipo           = 'OTRO',
                registrado_por = usuario,
            )
        if reserva.opcion_checkout and reserva.opcion_checkout.cargo_extra > 0:
            CargoEstancia.objects.create(
                estancia       = estancia,
                concepto       = f'Late check-out — {reserva.opcion_checkout.nombre}',
                monto          = reserva.opcion_checkout.cargo_extra,
                tipo           = 'OTRO',
                registrado_por = usuario,
            )
        # Crear folio — siempre ABIERTO para extras
        folio = Folio.objects.create(estancia=estancia)
        folio.recalcular()

        # Cambiar estados
        reserva.estado    = 'CHECKIN'
        habitacion.estado = 'OCUPADA'
        reserva.save()
        habitacion.save()

        return estancia

    @staticmethod
    @transaction.atomic
    def checkout(estancia_id: int, usuario) -> Estancia:
        from apps.recepcion.models import Habitacion

        try:
            estancia = Estancia.objects.select_related(
                'reserva', 'habitacion'
            ).get(pk=estancia_id)
        except Estancia.DoesNotExist:
            raise EstanciaNoEncontrada(f'Estancia {estancia_id} no encontrada.')

        # Verificar folio sin deuda
        folio = estancia.folio
        if folio.tiene_deuda:
            raise DeudasPendientesError(
                f'El folio tiene una deuda pendiente de S/ {folio.total}. '
                f'Debe pagarse antes del checkout.'
            )

        # Cambiar estados
        estancia.estado            = 'FINALIZADA'
        estancia.fecha_checkout    = timezone.now()
        estancia.reserva.estado    = 'CHECKOUT'
        estancia.habitacion.estado = 'LIMPIEZA'

        estancia.save()
        estancia.reserva.save()
        estancia.habitacion.save()

        # Crear tarea de limpieza automáticamente
        from apps.housekeeping.models import TareaLimpieza
        TareaLimpieza.objects.create(
            habitacion = estancia.habitacion,
            prioridad  = 'ALTA',
        )

        return estancia


class FolioService:

    @staticmethod
    def agregar_cargo(estancia_id: int, concepto: str, monto, tipo: str, usuario) -> CargoEstancia:
        estancia = Estancia.objects.get(pk=estancia_id)
        folio    = estancia.folio

        if folio.estado == 'CERRADO':
            raise FolioCerrado('No se pueden agregar cargos a un folio cerrado.')

        cargo = CargoEstancia.objects.create(
            estancia       = estancia,
            concepto       = concepto,
            monto          = monto,
            tipo           = tipo,
            registrado_por = usuario,
        )
        folio.recalcular()
        return cargo

    @staticmethod
    def pagar(estancia_id: int, usuario) -> Folio:
        estancia = Estancia.objects.get(pk=estancia_id)
        folio    = estancia.folio

        if folio.estado == 'CERRADO':
            raise FolioCerrado('El folio ya está pagado.')

        folio.estado     = 'PAGADO'
        folio.fecha_pago = timezone.now()
        folio.save()
        return folio