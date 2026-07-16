from django.db import models
from django.conf import settings
from utils.models import ModeloBase


class Huesped(ModeloBase):
    TIPO_DOC = [('DNI', 'DNI'), ('CE', 'Carnet de Extranjería'), ('PAS', 'Pasaporte')]

    tipo_doc      = models.CharField(max_length=3, choices=TIPO_DOC, default='DNI')
    num_doc       = models.CharField(max_length=20, unique=True)
    nombres       = models.CharField(max_length=100)
    apellidos     = models.CharField(max_length=100)
    email         = models.EmailField(blank=True)
    telefono      = models.CharField(max_length=15, blank=True)
    nacionalidad  = models.CharField(max_length=50, default='Peruana')
    acepta_emails = models.BooleanField(default=False)
    usuario       = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='huesped'
    )

    class Meta:
        verbose_name        = 'Huésped'
        verbose_name_plural = 'Huéspedes'
        ordering            = ['apellidos', 'nombres']

    def __str__(self):
        return f'{self.nombres} {self.apellidos} ({self.num_doc})'

    @property
    def nombre_completo(self):
        return f'{self.nombres} {self.apellidos}'


class Tarifa(ModeloBase):
    tipo_habitacion = models.ForeignKey(
        'recepcion.TipoHabitacion',
        on_delete=models.CASCADE,
        related_name='tarifas'
    )
    precio_noche    = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_inicio    = models.DateField()
    fecha_fin       = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name        = 'Tarifa'
        verbose_name_plural = 'Tarifas'
        ordering            = ['-fecha_inicio']

    def __str__(self):
        return f'{self.tipo_habitacion} — S/ {self.precio_noche}'

    @staticmethod
    def get_precio_vigente(tipo, fecha_entrada, fecha_salida):
        tarifa = Tarifa.objects.filter(
            tipo_habitacion=tipo,
            fecha_inicio__lte=fecha_entrada,
        ).filter(
            models.Q(fecha_fin__isnull=True) | models.Q(fecha_fin__gte=fecha_salida)
        ).order_by('-fecha_inicio').first()
        return tarifa.precio_noche if tarifa else tipo.precio_base


class Reserva(ModeloBase):
    ESTADOS = [
        ('PENDIENTE',  'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('CHECKIN',    'Check-in'),
        ('CHECKOUT',   'Check-out'),
        ('CANCELADA',  'Cancelada'),
    ]
    ORIGENES = [
        ('WEB',     'Web'),
        ('DIRECTO', 'Directo'),
        ('AGENCIA', 'Agencia'),
    ]

    hotel           = models.ForeignKey('recepcion.Hotel',          on_delete=models.CASCADE,  related_name='reservas')
    huesped         = models.ForeignKey(Huesped,                    on_delete=models.CASCADE,  related_name='reservas')
    tipo_habitacion = models.ForeignKey('recepcion.TipoHabitacion', on_delete=models.CASCADE,  related_name='reservas')
    habitacion      = models.ForeignKey('recepcion.Habitacion',     on_delete=models.SET_NULL, null=True, blank=True, related_name='reservas')
    fecha_entrada   = models.DateField()
    fecha_salida    = models.DateField()
    num_adultos     = models.PositiveIntegerField(default=1)
    num_ninos       = models.PositiveIntegerField(default=0)
    estado          = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE', db_index=True)
    origen          = models.CharField(max_length=20, choices=ORIGENES, default='DIRECTO')
    precio_total    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    observaciones    = models.TextField(blank=True)
    opcion_checkin   = models.ForeignKey(
        'recepcion.OpcionCheckin',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reservas_checkin'
    )
    opcion_checkout  = models.ForeignKey(
        'recepcion.OpcionCheckin',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reservas_checkout'
    )
    creado_por      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reservas_creadas'
    )

    class Meta:
        verbose_name        = 'Reserva'
        verbose_name_plural = 'Reservas'
        ordering            = ['-creado_en']

    def __str__(self):
        return f'R-{self.pk} — {self.huesped} ({self.estado})'

    @property
    def num_noches(self):
        return (self.fecha_salida - self.fecha_entrada).days

    @property
    def total_con_extras(self):
        extra = 0
        if self.opcion_checkin and self.opcion_checkin.cargo_extra:
            extra += self.opcion_checkin.cargo_extra
        if self.opcion_checkout and self.opcion_checkout.cargo_extra:
            extra += self.opcion_checkout.cargo_extra
        return self.precio_total + extra


class Estancia(ModeloBase):
    ESTADOS = [
        ('ACTIVA',     'Activa'),
        ('FINALIZADA', 'Finalizada'),
    ]

    reserva        = models.OneToOneField(Reserva,             on_delete=models.CASCADE, related_name='estancia')
    habitacion     = models.ForeignKey('recepcion.Habitacion', on_delete=models.CASCADE, related_name='estancias')
    estado         = models.CharField(max_length=20, choices=ESTADOS, default='ACTIVA')
    fecha_checkin  = models.DateTimeField(auto_now_add=True)
    fecha_checkout = models.DateTimeField(null=True, blank=True)
    atendido_por   = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='estancias_atendidas'
    )

    class Meta:
        verbose_name        = 'Estancia'
        verbose_name_plural = 'Estancias'

    def __str__(self):
        return f'Estancia {self.pk} — {self.reserva}'


class CargoEstancia(ModeloBase):
    TIPOS = [
        ('HABITACION',  'Habitación'),
        ('RESTAURANTE', 'Restaurante'),
        ('MINIBAR',     'Minibar'),
        ('LAVANDERIA',  'Lavandería'),
        ('OTRO',        'Otro'),
    ]

    estancia       = models.ForeignKey(Estancia, on_delete=models.CASCADE, related_name='cargos')
    concepto       = models.CharField(max_length=200)
    monto          = models.DecimalField(max_digits=10, decimal_places=2)
    tipo           = models.CharField(max_length=20, choices=TIPOS, default='OTRO')
    fecha          = models.DateTimeField(auto_now_add=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='cargos_registrados'
    )

    class Meta:
        verbose_name        = 'Cargo de Estancia'
        verbose_name_plural = 'Cargos de Estancia'
        ordering            = ['fecha']

    def __str__(self):
        return f'{self.concepto} — S/ {self.monto}'


class Folio(ModeloBase):
    ESTADOS = [
        ('ABIERTO', 'Abierto'),
        ('PAGADO',  'Pagado'),
        ('CERRADO', 'Cerrado'),
    ]
    METODOS_PAGO = [
        ('EFECTIVO',      'Efectivo'),
        ('TARJETA',       'Tarjeta'),
        ('YAPE',          'Yape'),
        ('TRANSFERENCIA', 'Transferencia'),
    ]

    estancia    = models.OneToOneField(Estancia, on_delete=models.CASCADE, related_name='folio')
    total       = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado      = models.CharField(max_length=20, choices=ESTADOS, default='ABIERTO')
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, null=True, blank=True)
    fecha_pago  = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name        = 'Folio'
        verbose_name_plural = 'Folios'

    def __str__(self):
        return f'Folio {self.pk} — {self.estancia}'

    @property
    def tiene_deuda(self):
        return self.estado != 'PAGADO'

    def recalcular(self):
        total      = self.estancia.cargos.aggregate(t=models.Sum('monto'))['t'] or 0
        self.total = total
        self.save(update_fields=['total', 'actualizado_en'])