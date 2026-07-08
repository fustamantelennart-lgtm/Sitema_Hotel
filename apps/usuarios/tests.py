from django.test import TestCase, Client
from django.urls import reverse
from apps.usuarios.models import Usuario


class UsuarioModelTest(TestCase):

    def test_crear_usuario_recepcionista(self):
        user = Usuario.objects.create_user(
            username='recep_test',
            password='test1234',
            rol='recepcionista',
        )
        self.assertTrue(user.es_recepcionista)
        self.assertFalse(user.es_admin)
        self.assertFalse(user.es_housekeeping)

    def test_crear_usuario_admin(self):
        user = Usuario.objects.create_user(
            username='admin_test',
            password='test1234',
            rol='admin',
        )
        self.assertTrue(user.es_admin)

    def test_crear_usuario_housekeeping(self):
        user = Usuario.objects.create_user(
            username='hk_test',
            password='test1234',
            rol='housekeeping',
        )
        self.assertTrue(user.es_housekeeping)

    def test_login_valido(self):
        Usuario.objects.create_user(
            username='login_test',
            password='test1234',
            rol='recepcionista',
        )
        client = Client()
        response = client.post(reverse('usuarios:login'), {
            'username': 'login_test',
            'password': 'test1234',
        })
        self.assertEqual(response.status_code, 302)

    def test_login_invalido(self):
        client   = Client()
        response = client.post(reverse('usuarios:login'), {
            'username': 'noexiste',
            'password': 'wrongpass',
        })
        self.assertEqual(response.status_code, 200)

    def test_acceso_denegado_sin_login(self):
        client   = Client()
        response = client.get(reverse('reservas:lista'))
        self.assertNotEqual(response.status_code, 200)