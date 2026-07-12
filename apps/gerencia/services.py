from django.utils import timezone
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth


class GerenciaService:

    @staticmethod
    def get_kpis(hotel):
        from apps.recepcion.models import Habitacion
        from apps.reservas.models import Reserva

        hoy  = timezone.now().date()
        mes  = hoy.month
        anio = hoy.year

        habitaciones  = Habitacion.objects.filter(hotel=hotel)
        total         = habitaciones.count()
        ocupadas      = habitaciones.filter(estado='OCUPADA').count()
        disponibles   = habitaciones.filter(estado='DISPONIBLE').count()
        limpieza      = habitaciones.filter(estado='LIMPIEZA').count()
        mantenimiento = habitaciones.filter(estado='MANTENIMIENTO').count()
        ocupacion_pct = round((ocupadas / total * 100), 1) if total else 0

        total_reservas = Reserva.objects.count()
        ingresos = Reserva.objects.filter(
            estado__in=['CONFIRMADA', 'CHECKIN', 'CHECKOUT'],
            creado_en__month=mes,
            creado_en__year=anio,
        ).aggregate(t=Sum('precio_total'))['t'] or 0

        return {
            'total_reservas': total_reservas,
            'ocupadas':       ocupadas,
            'ocupacion_pct':  ocupacion_pct,
            'ingresos':       ingresos,
            'disponibles':    disponibles,
            'limpieza':       limpieza,
            'mantenimiento':  mantenimiento,
            'total':          total,
        }

    @staticmethod
    def get_grafico_reservas():
        from apps.reservas.models import Reserva
        from dateutil.relativedelta import relativedelta

        hoy            = timezone.now().date()
        meses_labels   = []
        meses_ocupacion = []

        for i in range(5, -1, -1):
            fecha = hoy - relativedelta(months=i)
            label = fecha.strftime('%b %Y')
            count = Reserva.objects.filter(
                estado__in=['CONFIRMADA', 'CHECKIN', 'CHECKOUT'],
                creado_en__month=fecha.month,
                creado_en__year=fecha.year,
            ).count()
            meses_labels.append(label)
            meses_ocupacion.append(count)

        return meses_labels, meses_ocupacion

    @staticmethod
    def get_grafico_tipos():
        from apps.reservas.models import Reserva

        por_tipo = Reserva.objects.filter(
            estado__in=['CONFIRMADA', 'CHECKIN', 'CHECKOUT']
        ).values('tipo_habitacion__nombre').annotate(
            ingresos=Sum('precio_total')
        ).order_by('-ingresos')

        tipo_labels   = [t['tipo_habitacion__nombre'] for t in por_tipo]
        tipo_ingresos = [float(t['ingresos'] or 0) for t in por_tipo]
        return tipo_labels, tipo_ingresos

    @staticmethod
    def get_reporte_periodo(fecha_inicio, fecha_fin):
        from apps.reservas.models import Reserva

        reservas_qs = Reserva.objects.filter(
            creado_en__date__gte=fecha_inicio,
            creado_en__date__lte=fecha_fin,
        )

        resumen = {
            'total':       reservas_qs.count(),
            'confirmadas': reservas_qs.filter(estado='CONFIRMADA').count(),
            'checkin':     reservas_qs.filter(estado='CHECKIN').count(),
            'checkout':    reservas_qs.filter(estado='CHECKOUT').count(),
            'canceladas':  reservas_qs.filter(estado='CANCELADA').count(),
            'ingresos':    reservas_qs.filter(
                estado__in=['CONFIRMADA', 'CHECKIN', 'CHECKOUT']
            ).aggregate(t=Sum('precio_total'))['t'] or 0,
        }

        por_tipo = reservas_qs.filter(
            estado__in=['CONFIRMADA', 'CHECKIN', 'CHECKOUT']
        ).values('tipo_habitacion__nombre').annotate(
            total=Count('id'),
            ingresos=Sum('precio_total'),
        ).order_by('-total')

        return resumen, por_tipo