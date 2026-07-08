from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta
from apps.usuarios.models import Usuario
from apps.recepcion.models import Hotel, TipoHabitacion, Habitacion
from apps.reservas.models import Huesped, Reserva, Estancia, Folio, CargoEstancia


class HuespedModelTest(TestCase):

    def setUp(self):
        self.huesped = Huesped.objects.create(
            tipo_doc  = 'DNI',
            num_doc   = '12345678',
            nombres   = 'Juan',
            apellidos = 'Pérez García',
            email     = 'juan@test.com',
            telefono  = '999999999',
        )

    def test_nombre_completo(self):
        self.assertEqual(self.huesped.nombre_completo, 'Juan Pérez García')

    def test_str(self):
        self.assertIn('Juan', str(self.huesped))

    def test_num_doc_unico(self):
        with self.assertRaises(Exception):
            Huesped.objects.create(
                tipo_doc  = 'DNI',
                num_doc   = '12345678',
                nombres   = 'Otro',
                apellidos = 'Apellido',
            )


class ReservaModelTest(TestCase):

    def setUp(self):
        self.hotel = Hotel.objects.create(
            nombre    = 'Hotel Test',
            ruc       = '20123456789',
            direccion = 'Av. Test 123',
            estrellas = 3,
            telefono  = '074000000',
        )
        self.tipo = TipoHabitacion.objects.create(
            hotel       = self.hotel,
            nombre      = 'Estándar',
            capacidad   = 2,
            precio_base = 200,
        )
        self.habitacion = Habitacion.objects.create(
            hotel  = self.hotel,
            tipo   = self.tipo,
            numero = '101',
            piso   = 1,
        )
        self.huesped = Huesped.objects.create(
            tipo_doc  = 'DNI',
            num_doc   = '87654321',
            nombres   = 'María',
            apellidos = 'López',
        )
        self.user = Usuario.objects.create_user(
            username = 'recep1',
            password = 'test1234',
            rol      = 'recepcionista',
        )
        self.reserva = Reserva.objects.create(
            hotel           = self.hotel,
            huesped         = self.huesped,
            tipo_habitacion = self.tipo,
            fecha_entrada   = date.today() + timedelta(days=1),
            fecha_salida    = date.today() + timedelta(days=3),
            num_adultos     = 2,
            estado          = 'CONFIRMADA',
            precio_total    = 400,
            origen          = 'DIRECTO',
            creado_por      = self.user,
        )

    def test_num_noches(self):
        self.assertEqual(self.reserva.num_noches, 2)

    def test_estado_inicial(self):
        self.assertEqual(self.reserva.estado, 'CONFIRMADA')

    def test_precio_total(self):
        self.assertEqual(float(self.reserva.precio_total), 400.0)

    def test_str_reserva(self):
        self.assertIn('María', str(self.reserva))


class ValidacionReservaFormTest(TestCase):

    def setUp(self):
        self.hotel = Hotel.objects.create(
            nombre='Hotel Test', ruc='20111111111',
            direccion='Test', estrellas=3, telefono='000'
        )
        self.tipo = TipoHabitacion.objects.create(
            hotel=self.hotel, nombre='Simple',
            capacidad=2, precio_base=100
        )
        Habitacion.objects.create(
            hotel=self.hotel, tipo=self.tipo,
            numero='201', piso=2
        )

    def test_fecha_pasada_invalida(self):
        from apps.reservas.forms import ReservaPresencialForm
        form = ReservaPresencialForm({
            'tipo_doc':       'DNI',
            'num_doc':        '11111111',
            'nombres':        'Test',
            'apellidos':      'User',
            'tipo_habitacion': self.tipo.pk,
            'fecha_entrada':  str(date.today() - timedelta(days=1)),
            'fecha_salida':   str(date.today() + timedelta(days=1)),
            'num_adultos':    1,
            'num_ninos':      0,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_entrada', form.errors)

    def test_capacidad_excedida(self):
        from apps.reservas.forms import ReservaPresencialForm
        form = ReservaPresencialForm({
            'tipo_doc':       'DNI',
            'num_doc':        '11111112',
            'nombres':        'Test',
            'apellidos':      'User',
            'tipo_habitacion': self.tipo.pk,
            'fecha_entrada':  str(date.today() + timedelta(days=1)),
            'fecha_salida':   str(date.today() + timedelta(days=3)),
            'num_adultos':    10,
            'num_ninos':      5,
        })
        self.assertFalse(form.is_valid())

    def test_fechas_validas(self):
        from apps.reservas.forms import ReservaPresencialForm
        form = ReservaPresencialForm({
            'tipo_doc':       'DNI',
            'num_doc':        '11111113',
            'nombres':        'Test',
            'apellidos':      'User',
            'tipo_habitacion': self.tipo.pk,
            'fecha_entrada':  str(date.today() + timedelta(days=5)),
            'fecha_salida':   str(date.today() + timedelta(days=7)),
            'num_adultos':    1,
            'num_ninos':      0,
        })
        self.assertTrue(form.is_valid())

    def test_fecha_salida_antes_entrada(self):
        from apps.reservas.forms import ReservaPresencialForm
        form = ReservaPresencialForm({
            'tipo_doc':       'DNI',
            'num_doc':        '11111114',
            'nombres':        'Test',
            'apellidos':      'User',
            'tipo_habitacion': self.tipo.pk,
            'fecha_entrada':  str(date.today() + timedelta(days=5)),
            'fecha_salida':   str(date.today() + timedelta(days=3)),
            'num_adultos':    1,
            'num_ninos':      0,
        })
        self.assertFalse(form.is_valid())


class CheckinCheckoutTest(TestCase):

    def setUp(self):
        self.hotel = Hotel.objects.create(
            nombre='Hotel Test', ruc='20222222222',
            direccion='Test', estrellas=3, telefono='000'
        )
        self.tipo = TipoHabitacion.objects.create(
            hotel=self.hotel, nombre='Doble',
            capacidad=2, precio_base=300
        )
        self.habitacion = Habitacion.objects.create(
            hotel=self.hotel, tipo=self.tipo,
            numero='301', piso=3
        )
        self.huesped = Huesped.objects.create(
            tipo_doc='DNI', num_doc='99999999',
            nombres='Carlos', apellidos='Ruiz',
        )
        self.user = Usuario.objects.create_user(
            username='recep2', password='test1234',
            rol='recepcionista',
        )
        self.reserva = Reserva.objects.create(
            hotel=self.hotel, huesped=self.huesped,
            tipo_habitacion=self.tipo,
            fecha_entrada=date.today(),
            fecha_salida=date.today() + timedelta(days=2),
            num_adultos=1, estado='CONFIRMADA',
            precio_total=600, origen='DIRECTO',
            creado_por=self.user,
        )

    def test_checkin_cambia_estado_habitacion(self):
        estancia = Estancia.objects.create(
            reserva=self.reserva,
            habitacion=self.habitacion,
            atendido_por=self.user,
        )
        CargoEstancia.objects.create(
            estancia=estancia,
            concepto='Habitación',
            monto=600,
            tipo='HABITACION',
            registrado_por=self.user,
        )
        folio = Folio.objects.create(estancia=estancia)
        folio.recalcular()

        self.habitacion.estado = 'OCUPADA'
        self.habitacion.save()
        self.reserva.estado    = 'CHECKIN'
        self.reserva.save()

        self.habitacion.refresh_from_db()
        self.reserva.refresh_from_db()
        self.assertEqual(self.habitacion.estado, 'OCUPADA')
        self.assertEqual(self.reserva.estado, 'CHECKIN')

    def test_checkout_pone_habitacion_en_limpieza(self):
        estancia = Estancia.objects.create(
            reserva=self.reserva,
            habitacion=self.habitacion,
            atendido_por=self.user,
        )
        CargoEstancia.objects.create(
            estancia=estancia, concepto='Habitación',
            monto=600, tipo='HABITACION',
            registrado_por=self.user,
        )
        folio = Folio.objects.create(estancia=estancia)
        folio.recalcular()

        folio.estado = 'PAGADO'
        folio.fecha_pago = timezone.now()
        folio.save()
        estancia.estado = 'FINALIZADA'
        estancia.save()
        self.habitacion.estado = 'LIMPIEZA'
        self.habitacion.save()

        self.habitacion.refresh_from_db()
        self.assertEqual(self.habitacion.estado, 'LIMPIEZA')