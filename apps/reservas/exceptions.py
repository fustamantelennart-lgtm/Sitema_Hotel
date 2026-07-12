class AppError(Exception):
    """Base de todas las excepciones de la aplicación."""
    pass


class ReglaNegocioViolada(AppError):
    pass


class RecursoNoEncontrado(AppError):
    pass


# ===== RESERVAS =====
class ReservaNoConfirmada(ReglaNegocioViolada):
    pass


class SolapamientoReservas(ReglaNegocioViolada):
    pass


class FechaPasadaError(ReglaNegocioViolada):
    pass


class CapacidadExcedida(ReglaNegocioViolada):
    pass


# ===== ESTANCIA =====
class HabitacionNoDisponible(ReglaNegocioViolada):
    pass


class DeudasPendientesError(ReglaNegocioViolada):
    pass


class EstanciaNoEncontrada(RecursoNoEncontrado):
    pass


# ===== HOUSEKEEPING =====
class TareaYaIniciada(ReglaNegocioViolada):
    pass


class TareaYaCompletada(ReglaNegocioViolada):
    pass


# ===== FOLIO =====
class FolioCerrado(ReglaNegocioViolada):
    pass