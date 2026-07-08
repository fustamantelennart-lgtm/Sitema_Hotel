from django.test import TestCase, Client
from django.urls import reverse
from apps.usuarios.models import Usuario
from apps.recepcion.models import Hotel, TipoHabitacion, Habitacion
from apps.housekeeping.models import TareaLimpieza


class HousekeepingViewTest(TestCase):

    def setUp(self):
        self.hotel = Hotel.objects.create(
            nombre='Hotel Test', ruc='20444444444',
            direccion='Test', estrellas=3, telefono='000'
        )
        self.tipo = TipoHabitacion.objects.create(
            hotel=self.hotel, nombre='Simple',
            capacidad=1, precio_base=100
        )
        self.habitacion = Habitacion.objects.create(
            hotel=self.hotel, tipo=self.tipo,
            numero='501', piso=5, estado='LIMPIEZA'
        )
        self.user_hk = Usuario.objects.create_user(
            username='hk_view', password='test1234',
            rol='housekeeping'
        )
        self.user_admin = Usuario.objects.create_user(
            username='admin_view', password='test1234',
            rol='admin'
        )
        self.tarea = TareaLimpieza.objects.create(
            habitacion=self.habitacion,
            prioridad='ALTA',
        )
        self.client = Client()

    def test_panel_requiere_login(self):
        response = self.client.get(reverse('housekeeping:panel'))
        self.assertNotEqual(response.status_code, 200)

    def test_panel_accesible_con_login(self):
        self.client.login(username='hk_view', password='test1234')
        response = self.client.get(reverse('housekeeping:panel'))
        self.assertEqual(response.status_code, 200)

    def test_iniciar_tarea(self):
        self.client.login(username='hk_view', password='test1234')
        response = self.client.post(
            reverse('housekeeping:iniciar', args=[self.tarea.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.tarea.refresh_from_db()
        self.assertEqual(self.tarea.estado, 'EN_PROCESO')

    def test_completar_tarea(self):
        self.tarea.estado = 'EN_PROCESO'
        self.tarea.save()
        self.client.login(username='hk_view', password='test1234')
        response = self.client.post(
            reverse('housekeeping:completar', args=[self.tarea.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.tarea.refresh_from_db()
        self.assertEqual(self.tarea.estado, 'LISTA')
        self.habitacion.refresh_from_db()
        self.assertEqual(self.habitacion.estado, 'DISPONIBLE')

    def test_historial_accesible(self):
        self.client.login(username='hk_view', password='test1234')
        response = self.client.get(reverse('housekeeping:historial'))
        self.assertEqual(response.status_code, 200)

    def test_tarea_model_str(self):
        self.assertIn('501', str(self.tarea))

    def test_tarea_prioridad_alta(self):
        self.assertEqual(self.tarea.prioridad, 'ALTA')