from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from apps.usuarios.decorators import rol_requerido


@login_required
@rol_requerido('admin')
def dashboard(request):
    from apps.reservas.models import Reserva, Estancia
    from apps.recepcion.models import Habitacion
    from django.db.models import Sum

    hoy = timezone.now().date()
    mes = hoy.month
    anio = hoy.year

    habitaciones  = Habitacion.objects.all()
    total         = habitaciones.count()
    ocupadas      = habitaciones.filter(estado='OCUPADA').count()
    ocupacion_pct = round((ocupadas / total * 100), 1) if total else 0

    total_reservas = Reserva.objects.count()
    ingresos = Reserva.objects.filter(
        estado__in=['CONFIRMADA', 'CHECKIN', 'CHECKOUT'],
        creado_en__month=mes,
        creado_en__year=anio,
    ).aggregate(t=Sum('precio_total'))['t'] or 0

    return render(request, 'gerencia/dashboard.html', {
        'total_reservas': total_reservas,
        'ocupadas':       ocupadas,
        'ocupacion_pct':  ocupacion_pct,
        'ingresos':       ingresos,
    })


@login_required
@rol_requerido('admin')
def ocupacion(request):
    from apps.reservas.models import Reserva
    from django.db.models import Count, Sum
    from django.db.models.functions import TruncMonth

    datos_qs = Reserva.objects.filter(
        estado__in=['CONFIRMADA', 'CHECKIN', 'CHECKOUT']
    ).annotate(mes=TruncMonth('creado_en')).values('mes').annotate(
        reservas=Count('id'),
        ingresos=Sum('precio_total'),
    ).order_by('-mes')[:12]

    datos = []
    for d in datos_qs:
        noches = sum(
            r.num_noches for r in Reserva.objects.filter(
                estado__in=['CONFIRMADA', 'CHECKIN', 'CHECKOUT'],
                creado_en__month=d['mes'].month,
                creado_en__year=d['mes'].year,
            )
        )
        datos.append({
            'mes':      d['mes'].strftime('%B %Y'),
            'reservas': d['reservas'],
            'noches':   noches,
            'ingresos': d['ingresos'] or 0,
        })

    return render(request, 'gerencia/ocupacion.html', {'datos': datos})


@login_required
@rol_requerido('admin')
def usuarios(request):
    from apps.usuarios.models import Usuario
    usuarios = Usuario.objects.all().order_by('rol', 'username')
    return render(request, 'gerencia/usuarios.html', {'usuarios': usuarios})


@login_required
@rol_requerido('admin')
def reportes(request):
    from apps.reservas.models import Reserva, Estancia
    from django.db.models import Sum, Count

    hoy = timezone.now().date()

    reservas_mes = Reserva.objects.filter(
        creado_en__month=hoy.month,
        creado_en__year=hoy.year,
    )

    resumen = {
        'total':      reservas_mes.count(),
        'confirmadas': reservas_mes.filter(estado='CONFIRMADA').count(),
        'checkin':    reservas_mes.filter(estado='CHECKIN').count(),
        'checkout':   reservas_mes.filter(estado='CHECKOUT').count(),
        'canceladas': reservas_mes.filter(estado='CANCELADA').count(),
        'ingresos':   reservas_mes.filter(
            estado__in=['CONFIRMADA','CHECKIN','CHECKOUT']
        ).aggregate(t=Sum('precio_total'))['t'] or 0,
    }

    por_tipo = Reserva.objects.filter(
        estado__in=['CONFIRMADA','CHECKIN','CHECKOUT']
    ).values('tipo_habitacion__nombre').annotate(
        total=Count('id'),
        ingresos=Sum('precio_total'),
    ).order_by('-total')

    return render(request, 'gerencia/reportes.html', {
        'resumen':  resumen,
        'por_tipo': por_tipo,
        'mes':      hoy.strftime('%B %Y'),
    })