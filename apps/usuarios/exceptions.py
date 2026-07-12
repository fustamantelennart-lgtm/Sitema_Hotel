from apps.reservas.exceptions import ReglaNegocioViolada, RecursoNoEncontrado


class UsuarioYaExiste(ReglaNegocioViolada):
    pass


class CredencialesInvalidas(ReglaNegocioViolada):
    pass


class RolNoPermitido(ReglaNegocioViolada):
    pass


class UsuarioNoEncontrado(RecursoNoEncontrado):
    pass