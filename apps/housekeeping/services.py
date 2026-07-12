from django.utils import timezone
from .models import TareaLimpieza, IncidenteHabitacion
from .exceptions import TareaYaIniciada, TareaYaCompletada


class HousekeepingService:

    @staticmethod
    def iniciar_tarea(tarea_id: int, usuario) -> TareaLimpieza:
        tarea = TareaLimpieza.objects.select_related('habitacion').get(pk=tarea_id)

        if tarea.estado == 'EN_PROCESO':
            raise TareaYaIniciada(f'La tarea de Hab. {tarea.habitacion.numero} ya está en proceso.')

        if tarea.estado == 'LISTA':
            raise TareaYaCompletada(f'La tarea de Hab. {tarea.habitacion.numero} ya fue completada.')

        tarea.estado     = 'EN_PROCESO'
        tarea.asignada_a = usuario
        tarea.save()
        return tarea

    @staticmethod
    def completar_tarea(tarea_id: int) -> TareaLimpieza:
        tarea = TareaLimpieza.objects.select_related('habitacion').get(pk=tarea_id)

        if tarea.estado == 'LISTA':
            raise TareaYaCompletada(f'La tarea de Hab. {tarea.habitacion.numero} ya fue completada.')

        tarea.marcar_lista()
        return tarea

    @staticmethod
    def asignar_tarea(tarea_id: int, empleado_id: int, prioridad: str) -> TareaLimpieza:
        from apps.usuarios.models import Usuario
        tarea = TareaLimpieza.objects.get(pk=tarea_id)

        if empleado_id:
            tarea.asignada_a = Usuario.objects.get(pk=empleado_id)
        if prioridad:
            tarea.prioridad = prioridad
        tarea.save()
        return tarea

    @staticmethod
    def reportar_incidente(habitacion_id: int, tipo: str, descripcion: str,
                           monto_cobrar, usuario) -> IncidenteHabitacion:
        from apps.recepcion.models import Habitacion
        habitacion = Habitacion.objects.get(pk=habitacion_id)

        if habitacion.estado not in ['OCUPADA', 'LIMPIEZA']:
            from apps.reservas.exceptions import ReglaNegocioViolada
            raise ReglaNegocioViolada(
                f'Solo se pueden reportar incidentes en habitaciones OCUPADA o en LIMPIEZA.'
            )

        incidente = IncidenteHabitacion.objects.create(
            habitacion    = habitacion,
            tipo          = tipo,
            descripcion   = descripcion,
            monto_cobrar  = monto_cobrar or None,
            reportado_por = usuario,
        )
        return incidente

    @staticmethod
    def resolver_incidente(incidente_id: int) -> IncidenteHabitacion:
        incidente          = IncidenteHabitacion.objects.get(pk=incidente_id)
        incidente.resuelto = True
        incidente.save()
        return incidente