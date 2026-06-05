from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    ROL_CHOICES = [
        ('admin',          'Administrador'),
        ('recepcionista',  'Recepcionista'),
        ('housekeeping',   'Housekeeping'),
    ]
    rol      = models.CharField(max_length=20, choices=ROL_CHOICES, default='recepcionista')
    telefono = models.CharField(max_length=15, blank=True)

    class Meta:
        verbose_name        = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_rol_display()})"

    @property
    def es_admin(self):
        return self.rol == 'admin'

    @property
    def es_recepcionista(self):
        return self.rol in ('admin', 'recepcionista')

    @property
    def es_housekeeping(self):
        return self.rol in ('admin', 'housekeeping')
