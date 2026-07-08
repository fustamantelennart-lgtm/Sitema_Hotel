from django.test import TestCase, Client
from django.urls import reverse
from apps.usuarios.models import Usuario
from apps.recepcion.models import Hotel, TipoHabitacion, Habitacion


class GerenciaViewTest(TestCase):

    def setUp(self):
        self.admin = Usuario.objects.create_user(
            username='admin_ger', password='test1234',
            rol='admin'
        )
        self.recep = Usuario.objects.create_user(
            username='recep_ger', password='test1234',
            rol='recepcionista'
        )
        self.hotel = Hotel.objects.create(
            nombre='Hotel Test', ruc='20555555555',
            direccion='Test', estrellas=3, telefono='000'
        )
        self.client = Client()

    def test_dashboard_requiere_admin(self):
        self.client.login(username='recep_ger', password='test1234')
        response = self.client.get(reverse('gerencia:dashboard'))
        self.assertNotEqual(response.status_code, 200)

    def test_dashboard_accesible_admin(self):
        self.client.login(username='admin_ger', password='test1234')
        response = self.client.get(reverse('gerencia:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_reportes_accesible_admin(self):
        self.client.login(username='admin_ger', password='test1234')
        response = self.client.get(reverse('gerencia:reportes'))
        self.assertEqual(response.status_code, 200)

    def test_ocupacion_accesible_admin(self):
        self.client.login(username='admin_ger', password='test1234')
        response = self.client.get(reverse('gerencia:ocupacion'))
        self.assertEqual(response.status_code, 200)

    def test_usuarios_accesible_admin(self):
        self.client.login(username='admin_ger', password='test1234')
        response = self.client.get(reverse('gerencia:usuarios'))
        self.assertEqual(response.status_code, 200)

    def test_exportar_excel(self):
        self.client.login(username='admin_ger', password='test1234')
        response = self.client.get(reverse('gerencia:exportar_excel'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    def test_exportar_pdf(self):
        self.client.login(username='admin_ger', password='test1234')
        response = self.client.get(reverse('gerencia:exportar_pdf'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')