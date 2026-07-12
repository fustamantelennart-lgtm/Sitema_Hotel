from apps.reservas.exceptions import ReglaNegocioViolada, RecursoNoEncontrado


class HabitacionNoEncontrada(RecursoNoEncontrado):
    pass


class EstadoInvalido(ReglaNegocioViolada):
    pass


class HabitacionDuplicada(ReglaNegocioViolada):
    pass


class CambioEstadoNoPermitido(ReglaNegocioViolada):
    pass