from django.test import TestCase
from apps.recepcion.models import Hotel, TipoHabitacion, Habitacion


class HabitacionModelTest(TestCase):

    def setUp(self):
        self.hotel = Hotel.objects.create(
            nombre='Hotel Test', ruc='20333333333',
            direccion='Test', estrellas=4, telefono='000'
        )
        self.tipo = TipoHabitacion.objects.create(
            hotel=self.hotel, nombre='Suite',
            capacidad=3, precio_base=500
        )
        self.habitacion = Habitacion.objects.create(
            hotel=self.hotel, tipo=self.tipo,
            numero='401', piso=4,
        )

    def test_estado_inicial_disponible(self):
        self.assertEqual(self.habitacion.estado, 'DISPONIBLE')

    def test_property_disponible(self):
        self.assertTrue(self.habitacion.disponible)

    def test_property_color(self):
        self.assertEqual(self.habitacion.color, 'success')

    def test_cambio_estado(self):
        self.habitacion.estado = 'OCUPADA'
        self.habitacion.save()
        self.habitacion.refresh_from_db()
        self.assertEqual(self.habitacion.estado, 'OCUPADA')
        self.assertFalse(self.habitacion.disponible)

    def test_str_habitacion(self):
        self.assertIn('401', str(self.habitacion))

    def test_tipo_habitacion_str(self):
        self.assertIn('Suite', str(self.tipo))