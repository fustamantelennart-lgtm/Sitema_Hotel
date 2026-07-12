from apps.reservas.exceptions import ReglaNegocioViolada, RecursoNoEncontrado


class DisponibilidadAgotada(ReglaNegocioViolada):
    pass


class PagoInvalido(ReglaNegocioViolada):
    pass


class ReservaWebNoEncontrada(RecursoNoEncontrado):
    pass


class TarjetaRechazada(PagoInvalido):
    pass