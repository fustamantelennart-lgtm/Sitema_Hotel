from apps.reservas.exceptions import ReglaNegocioViolada, RecursoNoEncontrado


class TareaYaIniciada(ReglaNegocioViolada):
    pass


class TareaYaCompletada(ReglaNegocioViolada):
    pass


class IncidenteNoEncontrado(RecursoNoEncontrado):
    pass