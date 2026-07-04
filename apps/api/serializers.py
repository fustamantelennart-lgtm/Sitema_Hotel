from rest_framework import serializers
from apps.reservas.models import Reserva, Huesped, Estancia, CargoEstancia
from apps.recepcion.models import Hotel, TipoHabitacion, Habitacion


class HotelSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Hotel
        fields = ['id', 'nombre', 'ruc', 'direccion', 'estrellas', 'telefono', 'email']


class TipoHabitacionSerializer(serializers.ModelSerializer):
    hotel_nombre = serializers.CharField(source='hotel.nombre', read_only=True)

    class Meta:
        model  = TipoHabitacion
        fields = ['id', 'nombre', 'capacidad', 'precio_base', 'amenidades',
                  'descripcion', 'hotel', 'hotel_nombre']


class HabitacionSerializer(serializers.ModelSerializer):
    tipo_nombre  = serializers.CharField(source='tipo.nombre', read_only=True)
    hotel_nombre = serializers.CharField(source='hotel.nombre', read_only=True)

    class Meta:
        model  = Habitacion
        fields = ['id', 'numero', 'piso', 'estado', 'hotel', 'hotel_nombre',
                  'tipo', 'tipo_nombre', 'observaciones']


class HuespedSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Huesped
        fields = ['id', 'tipo_doc', 'num_doc', 'nombres', 'apellidos',
                  'email', 'telefono', 'nacionalidad']


class ReservaSerializer(serializers.ModelSerializer):
    huesped_nombre       = serializers.CharField(source='huesped.nombre_completo', read_only=True)
    tipo_habitacion_nombre = serializers.CharField(source='tipo_habitacion.nombre', read_only=True)
    hotel_nombre         = serializers.CharField(source='hotel.nombre', read_only=True)

    class Meta:
        model  = Reserva
        fields = [
            'id', 'estado', 'origen', 'fecha_entrada', 'fecha_salida',
            'num_noches', 'num_adultos', 'num_ninos', 'precio_total',
            'observaciones', 'creado_en',
            'hotel', 'hotel_nombre',
            'huesped', 'huesped_nombre',
            'tipo_habitacion', 'tipo_habitacion_nombre',
        ]
        read_only_fields = ['num_noches', 'precio_total', 'creado_en']


class CargoEstanciaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CargoEstancia
        fields = ['id', 'concepto', 'monto', 'tipo', 'fecha']