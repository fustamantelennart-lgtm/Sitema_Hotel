from django.contrib.auth import login, authenticate
from .models import Usuario
from .exceptions import UsuarioYaExiste, CredencialesInvalidas, UsuarioNoEncontrado


class UsuarioService:

    @staticmethod
    def registrar_cliente(form_data: dict, request) -> Usuario:
        from apps.reservas.models import Huesped

        email   = form_data.get('email')
        num_doc = form_data.get('num_doc')

        if Usuario.objects.filter(email=email).exists():
            raise UsuarioYaExiste(f'Ya existe una cuenta con el correo {email}.')

        user            = Usuario()
        user.email      = email
        user.username   = email
        user.first_name = form_data.get('first_name', '')
        user.last_name  = form_data.get('last_name', '')
        user.rol        = 'cliente'
        user.telefono   = form_data.get('telefono', '')
        user.set_password(form_data.get('password1'))
        user.save()

        # Vincular o crear huésped
        huesped = Huesped.objects.filter(num_doc=num_doc).first()
        if huesped:
            huesped.usuario   = user
            huesped.email     = email
            huesped.nombres   = user.first_name or huesped.nombres
            huesped.apellidos = user.last_name  or huesped.apellidos
            huesped.save()
        else:
            Huesped.objects.create(
                num_doc   = num_doc,
                tipo_doc  = 'DNI',
                nombres   = user.first_name,
                apellidos = user.last_name,
                email     = email,
                telefono  = user.telefono,
                usuario   = user,
            )

        login(request, user)
        return user

    @staticmethod
    def login_staff(username: str, password: str, request) -> Usuario:
        user = authenticate(request, username=username, password=password)
        if user is None:
            raise CredencialesInvalidas('Usuario o contraseña incorrectos.')
        login(request, user)
        return user

    @staticmethod
    def login_cliente(email: str, password: str, request) -> Usuario:
        try:
            user_obj = Usuario.objects.get(email=email, rol='cliente')
        except Usuario.DoesNotExist:
            raise UsuarioNoEncontrado('No existe una cuenta con ese correo.')

        user = authenticate(request, username=user_obj.username, password=password)
        if user is None:
            raise CredencialesInvalidas('Correo o contraseña incorrectos.')

        login(request, user)
        return user