from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

from apps.recepcion.models import Hotel, TipoHabitacion, Habitacion
from apps.reservas.models import Reserva, Huesped, Estancia, Tarifa
from .serializers import (
    HotelSerializer, TipoHabitacionSerializer, HabitacionSerializer,
    HuespedSerializer, ReservaSerializer, CargoEstanciaSerializer
)


class HotelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset         = Hotel.objects.all()
    serializer_class = HotelSerializer


class TipoHabitacionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset         = TipoHabitacion.objects.select_related('hotel').all()
    serializer_class = TipoHabitacionSerializer


class HabitacionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = HabitacionSerializer

    def get_queryset(self):
        qs = Habitacion.objects.select_related('hotel', 'tipo').all()
        estado = self.request.query_params.get('estado')
        if estado:
            qs = qs.filter(estado=estado.upper())
        return qs

    @action(detail=False, methods=['get'], url_path='disponibles')
    def disponibles(self, request):
        fecha_entrada = request.query_params.get('fecha_entrada')
        fecha_salida  = request.query_params.get('fecha_salida')
        tipo_id       = request.query_params.get('tipo')

        if not fecha_entrada or not fecha_salida:
            return Response(
                {'error': 'Se requieren fecha_entrada y fecha_salida'},
                status=status.HTTP_400_BAD_REQUEST
            )

        habitaciones = Habitacion.objects.select_related('tipo').filter(
            estado='DISPONIBLE'
        )
        if tipo_id:
            habitaciones = habitaciones.filter(tipo_id=tipo_id)

        resultado = []
        for hab in habitaciones:
            solapada = Reserva.objects.filter(
                habitacion=hab,
                estado__in=['PENDIENTE', 'CONFIRMADA', 'CHECKIN'],
            ).filter(
                Q(fecha_entrada__lt=fecha_salida) &
                Q(fecha_salida__gt=fecha_entrada)
            ).exists()
            if not solapada:
                resultado.append(hab)

        serializer = HabitacionSerializer(resultado, many=True)
        return Response(serializer.data)


class HuespedViewSet(viewsets.ModelViewSet):
    serializer_class = HuespedSerializer

    def get_queryset(self):
        qs  = Huesped.objects.all()
        q   = self.request.query_params.get('q')
        dni = self.request.query_params.get('dni')
        if q:
            qs = qs.filter(
                Q(nombres__icontains=q) |
                Q(apellidos__icontains=q) |
                Q(num_doc__icontains=q)
            )
        if dni:
            qs = qs.filter(num_doc=dni)
        return qs


class ReservaViewSet(viewsets.ModelViewSet):
    serializer_class = ReservaSerializer

    def get_queryset(self):
        qs     = Reserva.objects.select_related('huesped', 'tipo_habitacion', 'hotel').all()
        estado = self.request.query_params.get('estado')
        if estado:
            qs = qs.filter(estado=estado.upper())
        return qs.order_by('-creado_en')

    def perform_create(self, serializer):
        from apps.recepcion.models import Hotel
        hotel        = Hotel.objects.first()
        tipo         = serializer.validated_data['tipo_habitacion']
        fe           = serializer.validated_data['fecha_entrada']
        fs           = serializer.validated_data['fecha_salida']
        precio_noche = Tarifa.get_precio_vigente(tipo, fe, fs)
        noches       = (fs - fe).days
        serializer.save(
            hotel        = hotel,
            precio_total = precio_noche * noches,
            creado_por   = self.request.user,
            estado       = 'CONFIRMADA',
        )