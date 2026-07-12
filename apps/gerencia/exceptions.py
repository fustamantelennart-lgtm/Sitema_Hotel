from apps.reservas.exceptions import ReglaNegocioViolada, RecursoNoEncontrado


class ReporteVacio(RecursoNoEncontrado):
    pass


class PeriodoInvalido(ReglaNegocioViolada):
    pass


class ExportacionError(ReglaNegocioViolada):
    pass