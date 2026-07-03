from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .forms import RegistroClienteForm, LoginClienteForm
from .decorators import rol_requerido


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.rol == 'housekeeping':
                return redirect('housekeeping:lista')
            else:
                return redirect('recepcion:dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    return render(request, 'usuarios/login.html')

def logout_view(request):
    logout(request)
    return redirect('usuarios:login')


# ===== VISTAS CLIENTE =====

def registro_cliente(request):
    if request.user.is_authenticated and request.user.rol == 'cliente':
        return redirect('cuenta:perfil')

    form = RegistroClienteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f'¡Bienvenido, {user.first_name}! Tu cuenta fue creada.')
        return redirect('cuenta:perfil')

    return render(request, 'cuenta/registro.html', {'form': form})


def login_cliente(request):
    if request.user.is_authenticated and request.user.rol == 'cliente':
        return redirect('cuenta:perfil')

    form = LoginClienteForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            siguiente = request.POST.get('next') or '/web/'
            return redirect(siguiente)
        else:
            messages.error(request, 'Correo o contraseña incorrectos.')
            return redirect('/web/')

    return render(request, 'cuenta/login.html', {'form': form})


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