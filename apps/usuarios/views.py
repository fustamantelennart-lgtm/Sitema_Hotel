from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .forms import RegistroClienteForm, LoginClienteForm
from .services import UsuarioService
from .exceptions import UsuarioYaExiste, CredencialesInvalidas, UsuarioNoEncontrado
from .decorators import rol_requerido


def login_view(request):
    if request.method == 'POST':
        try:
            user = UsuarioService.login_staff(
                username = request.POST.get('username'),
                password = request.POST.get('password'),
                request  = request,
            )
            if user.rol == 'housekeeping':
                return redirect('housekeeping:panel')
            else:
                return redirect('recepcion:dashboard')
        except CredencialesInvalidas as e:
            messages.error(request, str(e))

    return render(request, 'usuarios/login.html')


def logout_view(request):
    logout(request)
    return redirect('usuarios:login')


# ===== VISTAS CLIENTE =====

def registro_cliente(request):
    if request.user.is_authenticated and request.user.rol == 'cliente':
        return redirect('cuenta:perfil')

    if request.method == 'POST':
        form = RegistroClienteForm(request.POST)
        if form.is_valid():
            try:
                user = UsuarioService.registrar_cliente(
                    form_data = {
                        'email':      form.cleaned_data['email'],
                        'first_name': form.cleaned_data.get('first_name', ''),
                        'last_name':  form.cleaned_data.get('last_name', ''),
                        'telefono':   form.cleaned_data.get('telefono', ''),
                        'num_doc':    form.cleaned_data['num_doc'],
                        'password1':  form.cleaned_data['password1'],
                    },
                    request = request,
                )
                messages.success(request, f'¡Bienvenido, {user.first_name}! Tu cuenta fue creada.')
                siguiente = request.POST.get('next', '')
                return redirect(siguiente if siguiente else 'cuenta:perfil')
            except UsuarioYaExiste as e:
                messages.error(request, str(e))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            next_url = request.POST.get('next', '/web/')
            return redirect(f'/web/?registro_error=1&next={next_url}')

    return redirect('/web/')


def registro_cliente_ajax(request):
    if request.method == 'POST':
        form = RegistroClienteForm(request.POST)
        if form.is_valid():
            try:
                user = UsuarioService.registrar_cliente(
                    form_data = {
                        'email':      form.cleaned_data['email'],
                        'first_name': form.cleaned_data.get('first_name', ''),
                        'last_name':  form.cleaned_data.get('last_name', ''),
                        'telefono':   form.cleaned_data.get('telefono', ''),
                        'num_doc':    form.cleaned_data['num_doc'],
                        'password1':  form.cleaned_data['password1'],
                    },
                    request = request,
                )
                siguiente = request.POST.get('next', '/web/')
                return JsonResponse({'ok': True, 'redirect': siguiente})
            except UsuarioYaExiste as e:
                return JsonResponse({'ok': False, 'errores': {'email': str(e)}})
        else:
            errores = {field: errors[0] for field, errors in form.errors.items()}
            return JsonResponse({'ok': False, 'errores': errores})
    return JsonResponse({'ok': False, 'errores': {'__all__': 'Método no permitido'}})


def login_cliente(request):
    if request.user.is_authenticated and request.user.rol == 'cliente':
        return redirect('cuenta:perfil')

    if request.method == 'POST':
        try:
            user     = UsuarioService.login_cliente(
                email    = request.POST.get('username'),
                password = request.POST.get('password'),
                request  = request,
            )
            siguiente = request.POST.get('next') or '/web/'
            return redirect(siguiente)
        except (CredencialesInvalidas, UsuarioNoEncontrado) as e:
            messages.error(request, str(e))
            return redirect('/web/')

    return render(request, 'cuenta/login.html')


def logout_cliente(request):
    logout(request)
    return redirect('/web/')


@login_required(login_url='/cuenta/login/')
def perfil_cliente(request):
    if request.user.rol != 'cliente':
        return redirect('/')

    from apps.reservas.models import Reserva
    try:
        huesped  = request.user.huesped
        reservas = (Reserva.objects
                    .filter(huesped=huesped)
                    .select_related('tipo_habitacion', 'habitacion')
                    .order_by('-fecha_entrada'))
    except Exception:
        reservas = []

    return render(request, 'cuenta/perfil.html', {'reservas': reservas})


@login_required(login_url='/cuenta/login/')
def cancelar_reserva(request, pk):
    from apps.reservas.models import Reserva
    reserva = get_object_or_404(
        Reserva,
        pk=pk,
        huesped__usuario=request.user,
        estado='PENDIENTE'
    )
    if request.method == 'POST':
        reserva.estado = 'CANCELADA'
        reserva.save()
        messages.success(request, 'Reserva cancelada correctamente.')
    return redirect('cuenta:perfil')