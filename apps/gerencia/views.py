from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from apps.usuarios.decorators import rol_requerido


@login_required
@rol_requerido('admin')
def dashboard(request):
    from apps.reservas.models import Reserva, Estancia
    from apps.recepcion.models import Habitacion, TipoHabitacion
    from django.db.models import Sum, Count
    from django.db.models.functions import TruncMonth
    import json

    hoy  = timezone.now().date()
    mes  = hoy.month
    anio = hoy.year

    habitaciones  = Habitacion.objects.all()
    total         = habitaciones.count()
    ocupadas      = habitaciones.filter(estado='OCUPADA').count()
    limpieza      = habitaciones.filter(estado='LIMPIEZA').count()
    disponibles   = habitaciones.filter(estado='DISPONIBLE').count()
    mantenimiento = habitaciones.filter(estado='MANTENIMIENTO').count()
    ocupacion_pct = round((ocupadas / total * 100), 1) if total else 0

    total_reservas = Reserva.objects.count()
    ingresos = Reserva.objects.filter(
        estado__in=['CONFIRMADA', 'CHECKIN', 'CHECKOUT'],
        creado_en__month=mes,
        creado_en__year=anio,
    ).aggregate(t=Sum('precio_total'))['t'] or 0

    # Datos para gráfico de ocupación últimos 6 meses
    from dateutil.relativedelta import relativedelta
    meses_labels = []
    meses_ocupacion = []
    for i in range(5, -1, -1):
        fecha = hoy - relativedelta(months=i)
        label = fecha.strftime('%b %Y')
        reservas_mes = Reserva.objects.filter(
            estado__in=['CONFIRMADA', 'CHECKIN', 'CHECKOUT'],
            creado_en__month=fecha.month,
            creado_en__year=fecha.year,
        ).count()
        meses_labels.append(label)
        meses_ocupacion.append(reservas_mes)

    # Datos para gráfico de estados de habitaciones
    estados_data = [disponibles, ocupadas, limpieza, mantenimiento]
    estados_labels = ['Disponible', 'Ocupada', 'En Limpieza', 'Mantenimiento']

    # Ingresos por tipo
    por_tipo = Reserva.objects.filter(
        estado__in=['CONFIRMADA', 'CHECKIN', 'CHECKOUT']
    ).values('tipo_habitacion__nombre').annotate(
        ingresos=Sum('precio_total')
    ).order_by('-ingresos')

    tipo_labels  = [t['tipo_habitacion__nombre'] for t in por_tipo]
    tipo_ingresos = [float(t['ingresos'] or 0) for t in por_tipo]

    return render(request, 'gerencia/dashboard.html', {
        'total_reservas': total_reservas,
        'ocupadas':       ocupadas,
        'ocupacion_pct':  ocupacion_pct,
        'ingresos':       ingresos,
        'disponibles':    disponibles,
        'limpieza':       limpieza,
        'mantenimiento':  mantenimiento,
        'total':          total,
        'meses_labels':   json.dumps(meses_labels),
        'meses_ocupacion': json.dumps(meses_ocupacion),
        'estados_data':   json.dumps(estados_data),
        'estados_labels': json.dumps(estados_labels),
        'tipo_labels':    json.dumps(tipo_labels),
        'tipo_ingresos':  json.dumps(tipo_ingresos),
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