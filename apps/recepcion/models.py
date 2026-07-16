from django.db import models
import cloudinary.models
from utils.models import ModeloBase


class Hotel(ModeloBase):
    nombre    = models.CharField(max_length=200)
    ruc       = models.CharField(max_length=11, unique=True)
    direccion = models.TextField()
    estrellas = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 6)], default=3)
    telefono  = models.CharField(max_length=15)
    email     = models.EmailField(blank=True)

    class Meta:
        verbose_name = 'Hotel'

    def __str__(self):
        return self.nombre


class TipoHabitacion(ModeloBase):
    hotel       = models.ForeignKey(Hotel, on_delete=models.CASCADE,
                                    related_name='tipos_habitacion')
    nombre      = models.CharField(max_length=100)
    capacidad   = models.PositiveSmallIntegerField()
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    amenidades  = models.JSONField(default=list, blank=True,
                                   help_text='Ej: ["WiFi","TV","AC"]')
    descripcion = models.TextField(blank=True)
    imagen      = cloudinary.models.CloudinaryField('imagen', blank=True, null=True)

    class Meta:
        verbose_name        = 'Tipo de Habitación'
        verbose_name_plural = 'Tipos de Habitación'

    def __str__(self):
        return f"{self.nombre} — {self.hotel}"


class ImagenTipoHabitacion(ModeloBase):
    tipo    = models.ForeignKey(TipoHabitacion, on_delete=models.CASCADE,
                                related_name='imagenes')
    imagen  = cloudinary.models.CloudinaryField('imagen')
    orden   = models.PositiveSmallIntegerField(default=0)
    caption = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name        = 'Imagen'
        verbose_name_plural = 'Imágenes'
        ordering            = ['orden']

    def __str__(self):
        return f"Imagen {self.orden} — {self.tipo.nombre}"


class Habitacion(ModeloBase):
    ESTADO_CHOICES = [
        ('DISPONIBLE',    'Disponible'),
        ('OCUPADA',       'Ocupada'),
        ('LIMPIEZA',      'En Limpieza'),
        ('MANTENIMIENTO', 'Mantenimiento'),
    ]
    COLOR_MAP = {
        'DISPONIBLE':    'success',
        'OCUPADA':       'danger',
        'LIMPIEZA':      'warning',
        'MANTENIMIENTO': 'secondary',
    }

    hotel         = models.ForeignKey(Hotel, on_delete=models.CASCADE,
                                      related_name='habitaciones')
    tipo          = models.ForeignKey(TipoHabitacion, on_delete=models.PROTECT,
                                      related_name='habitaciones')
    numero        = models.CharField(max_length=10)
    piso          = models.PositiveSmallIntegerField()
    estado        = models.CharField(max_length=15, choices=ESTADO_CHOICES,
                                     default='DISPONIBLE')
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name        = 'Habitación'
        verbose_name_plural = 'Habitaciones'
        unique_together     = ('hotel', 'numero')
        ordering            = ['piso', 'numero']

    def __str__(self):
        return f"Hab. {self.numero} P{self.piso} ({self.get_estado_display()})"

    @property
    def color(self):
        return self.COLOR_MAP.get(self.estado, 'light')

    @property
    def disponible(self):
        return self.estado == 'DISPONIBLE'
    
class OpcionCheckin(ModeloBase):
    TIPO_CHOICES = [
        ('CHECKIN',  'Early Check-in'),
        ('CHECKOUT', 'Late Check-out'),
    ]
    hotel       = models.ForeignKey(Hotel, on_delete=models.CASCADE,
                                    related_name='opciones_checkin')
    tipo        = models.CharField(max_length=10, choices=TIPO_CHOICES)
    nombre      = models.CharField(max_length=100)
    hora        = models.TimeField()
    cargo_extra = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    activo      = models.BooleanField(default=True)

    class Meta:
        verbose_name        = 'Opción Check-in/out'
        verbose_name_plural = 'Opciones Check-in/out'
        ordering = ['tipo', 'cargo_extra', 'hora']

    def __str__(self):
        hora_fmt = self.hora.strftime('%I:%M %p') if self.hora else ''
        if self.cargo_extra > 0:
            return f'{self.nombre} ({hora_fmt}) — S/ {self.cargo_extra}'
        return f'{self.nombre} ({hora_fmt}) — Incluido'