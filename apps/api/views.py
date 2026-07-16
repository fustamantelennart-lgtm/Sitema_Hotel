from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q

from apps.recepcion.models import Hotel, TipoHabitacion, Habitacion
from apps.reservas.models import Reserva, Huesped, Estancia, Tarifa, Folio
from apps.reservas.services import EstanciaService, FolioService
from apps.reservas.exceptions import (
    ReservaNoConfirmada, HabitacionNoDisponible, DeudasPendientesError,
)
from .serializers import (
    HotelSerializer, TipoHabitacionSerializer, HabitacionSerializer,
    HuespedSerializer, ReservaSerializer, CargoEstanciaSerializer,
    EstanciaSerializer, FolioSerializer,
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

class ReservaCheckinView(APIView):
    """POST /api/reservas/{id}/checkin/"""

    def post(self, request, pk):
        habitacion_id = request.data.get('habitacion_id')
        if not habitacion_id:
            return Response(
                {'error': 'Se requiere habitacion_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            estancia = EstanciaService.checkin(
                reserva_id    = pk,
                habitacion_id = habitacion_id,
                usuario       = request.user,
            )
            return Response(
                EstanciaSerializer(estancia).data,
                status=status.HTTP_201_CREATED
            )
        except ReservaNoConfirmada as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except HabitacionNoDisponible as e:
            return Response({'error': str(e)}, status=status.HTTP_409_CONFLICT)


class EstanciaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EstanciaSerializer

    def get_queryset(self):
        qs     = Estancia.objects.select_related(
            'reserva', 'reserva__huesped', 'habitacion'
        ).all()
        estado = self.request.query_params.get('estado')
        if estado:
            qs = qs.filter(estado=estado.upper())
        return qs.order_by('-fecha_checkin')

    @action(detail=True, methods=['post'], url_path='checkout')
    def checkout(self, request, pk=None):
        try:
            estancia = EstanciaService.checkout(
                estancia_id = pk,
                usuario     = request.user,
            )
            return Response(EstanciaSerializer(estancia).data)
        except DeudasPendientesError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get', 'post'], url_path='folio')
    def folio(self, request, pk=None):
        estancia = self.get_object()
        folio    = estancia.folio

        if request.method == 'GET':
            return Response(FolioSerializer(folio).data)

        # POST -> agregar cargo al folio
        concepto = request.data.get('concepto')
        monto    = request.data.get('monto')
        tipo     = request.data.get('tipo', 'OTRO')

        if not concepto or not monto:
            return Response(
                {'error': 'Se requieren concepto y monto'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            FolioService.agregar_cargo(
                estancia_id = estancia.pk,
                concepto    = concepto,
                monto       = monto,
                tipo        = tipo,
                usuario     = request.user,
            )
            folio.refresh_from_db()
            return Response(
                FolioSerializer(folio).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class HousekeepingUpdateView(APIView):
    """PATCH /api/habitaciones/{id}/housekeeping/"""

    def patch(self, request, pk):
        estado_nuevo = request.data.get('estado')
        estados_validos = dict(Habitacion.ESTADO_CHOICES).keys()

        if estado_nuevo not in estados_validos:
            return Response(
                {'error': f'Estado inválido. Opciones: {list(estados_validos)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            habitacion = Habitacion.objects.get(pk=pk)
        except Habitacion.DoesNotExist:
            return Response({'error': 'Habitación no encontrada'}, status=404)

        habitacion.estado = estado_nuevo
        habitacion.save()
        return Response(HabitacionSerializer(habitacion).data)


class ReporteOcupacionView(APIView):
    """GET /api/reportes/ocupacion/?fecha=YYYY-MM-DD"""

    def get(self, request):
        from datetime import date

        fecha_str = request.query_params.get('fecha')
        fecha     = date.fromisoformat(fecha_str) if fecha_str else date.today()

        resultado = []
        for tipo in TipoHabitacion.objects.all():
            habitaciones = Habitacion.objects.filter(tipo=tipo)
            total_habs   = habitaciones.count()
            if total_habs == 0:
                continue

            ocupadas = Reserva.objects.filter(
                tipo_habitacion = tipo,
                estado__in      = ['CONFIRMADA', 'CHECKIN'],
                fecha_entrada__lte = fecha,
                fecha_salida__gt   = fecha,
            ).count()

            resultado.append({
                'tipo_habitacion': tipo.nombre,
                'total':           total_habs,
                'ocupadas':        ocupadas,
                'tasa_ocupacion':  round((ocupadas / total_habs) * 100, 1),
            })

        return Response({
            'fecha':      fecha.isoformat(),
            'ocupacion':  resultado,
        })