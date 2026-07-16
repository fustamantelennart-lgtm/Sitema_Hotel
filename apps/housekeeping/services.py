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
                           monto_cobrar, usuario, tarea_id=None) -> IncidenteHabitacion:
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

        # Si el incidente tiene monto a cobrar, buscar la estancia correcta
        # para agregar el cargo a su folio. Primero se intenta a través de
        # la tarea (funciona incluso si la habitación ya cambió de estancia
        # por un cambio de habitación), y si no, por la habitación actual.
        if monto_cobrar:
            estancia_activa = None
            if tarea_id:
                tarea_rel = TareaLimpieza.objects.filter(pk=tarea_id).select_related('estancia_relacionada').first()
                if tarea_rel and tarea_rel.estancia_relacionada and tarea_rel.estancia_relacionada.estado == 'ACTIVA':
                    estancia_activa = tarea_rel.estancia_relacionada
            if not estancia_activa:
                from apps.reservas.models import Estancia
                estancia_activa = Estancia.objects.filter(
                    habitacion=habitacion, estado='ACTIVA'
                ).select_related('folio').first()
            if estancia_activa:
                from apps.reservas.models import CargoEstancia
                CargoEstancia.objects.create(
                    estancia       = estancia_activa,
                    concepto       = f'{incidente.get_tipo_display()} — {descripcion}',
                    monto          = monto_cobrar,
                    tipo           = 'OTRO',
                    registrado_por = usuario,
                )
                estancia_activa.folio.recalcular()

        return incidente

    @staticmethod
    def resolver_incidente(incidente_id: int) -> IncidenteHabitacion:
        incidente          = IncidenteHabitacion.objects.get(pk=incidente_id)
        incidente.resuelto = True
        incidente.save()
        return incidente