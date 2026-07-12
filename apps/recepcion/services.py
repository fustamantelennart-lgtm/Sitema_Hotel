from .models import Hotel, Habitacion, TipoHabitacion
from .exceptions import (
    HabitacionNoEncontrada, EstadoInvalido,
    HabitacionDuplicada, CambioEstadoNoPermitido
)


class HabitacionService:

    ESTADOS_MANUALES = ['DISPONIBLE', 'LIMPIEZA', 'MANTENIMIENTO']

    @staticmethod
    def cambiar_estado(habitacion_id: int, nuevo_estado: str, usuario) -> Habitacion:
        try:
            habitacion = Habitacion.objects.get(pk=habitacion_id)
        except Habitacion.DoesNotExist:
            raise HabitacionNoEncontrada(f'Habitación {habitacion_id} no encontrada.')

        if nuevo_estado not in HabitacionService.ESTADOS_MANUALES:
            raise EstadoInvalido(f'Estado "{nuevo_estado}" no válido para cambio manual.')

        if habitacion.estado == 'OCUPADA' and not usuario.es_admin:
            raise CambioEstadoNoPermitido(
                'Solo el administrador puede liberar una habitación ocupada.'
            )

        habitacion.estado = nuevo_estado
        habitacion.save()
        return habitacion

    @staticmethod
    def crear_habitacion(numero: str, piso: int, tipo_id: int,
                         observaciones: str, hotel) -> Habitacion:
        if not numero or not piso or not tipo_id:
            raise EstadoInvalido('Completa todos los campos obligatorios.')

        if Habitacion.objects.filter(hotel=hotel, numero=numero).exists():
            raise HabitacionDuplicada(f'Ya existe la habitación {numero}.')

        try:
            tipo = TipoHabitacion.objects.get(pk=tipo_id)
        except TipoHabitacion.DoesNotExist:
            raise HabitacionNoEncontrada(f'Tipo de habitación no encontrado.')

        habitacion = Habitacion.objects.create(
            hotel         = hotel,
            tipo          = tipo,
            numero        = numero,
            piso          = int(piso),
            observaciones = observaciones or '',
        )
        return habitacion