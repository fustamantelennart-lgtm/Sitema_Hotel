import decimal
from django.db import models
from django.db.models import Q, Sum
from django.core.exceptions import ValidationError
from django.conf import settings
from apps.recepcion.models import Hotel, TipoHabitacion, Habitacion


class Huesped(models.Model):
    TIPO_DOC = [
        ('DNI',       'DNI'),
        ('PASAPORTE', 'Pasaporte'),
        ('CE',        'Carnet de Extranjería'),
    ]
    tipo_doc       = models.CharField(max_length=10, choices=TIPO_DOC, default='DNI')
    num_doc        = models.CharField(max_length=20, unique=True)
    nombres        = models.CharField(max_length=100)
    apellidos      = models.CharField(max_length=100)
    email          = models.EmailField(blank=True)
    telefono       = models.CharField(max_length=15, blank=True)
    nacionalidad   = models.CharField(max_length=60, default='Peruana')
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Huésped'
        verbose_name_plural = 'Huéspedes'
        ordering            = ['apellidos', 'nombres']

    def __str__(self):
        return f"{self.apellidos}, {self.nombres} — {self.num_doc}"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"


class Tarifa(models.Model):
    tipo_habitacion = models.ForeignKey(TipoHabitacion, on_delete=models.CASCADE,
                                         related_name='tarifas')
    nombre          = models.CharField(max_length=100,
                                       help_text='Ej: Temporada Alta Verano 2026')
    precio_noche    = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_inicio    = models.DateField()
    fecha_fin       = models.DateField()
    activa          = models.BooleanField(default=True)

    class Meta:
        verbose_name        = 'Tarifa'
        verbose_name_plural = 'Tarifas'
        ordering            = ['-fecha_inicio']

    def __str__(self):
        return f"{self.nombre} — S/ {self.precio_noche}/noche"

    def clean(self):
        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_inicio >= self.fecha_fin:
                raise ValidationError('fecha_inicio debe ser anterior a fecha_fin.')

    @classmethod
    def get_precio_vigente(cls, tipo_habitacion, fecha_entrada, fecha_salida):
        """Devuelve el precio/noche vigente para las fechas. Si no hay tarifa, usa precio_base."""
        tarifa = cls.objects.filter(
            tipo_habitacion=tipo_habitacion,
            activa=True,
            fecha_inicio__lte=fecha_entrada,
            fecha_fin__gte=fecha_salida,
        ).first()
        return tarifa.precio_noche if tarifa else tipo_habitacion.precio_base


class Reserva(models.Model):
    ESTADO = [
        ('PENDIENTE',  'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('CHECKIN',    'En Casa'),
        ('CHECKOUT',   'Checkout'),
        ('CANCELADA',  'Cancelada'),
        ('NO_SHOW',    'No Show'),
    ]
    ORIGEN = [
        ('DIRECTO',  'Directo'),
        ('TELEFONO', 'Teléfono'),
        ('WEB',      'Web'),
        ('AGENCIA',  'Agencia'),
    ]

    hotel           = models.ForeignKey(Hotel, on_delete=models.CASCADE,
                                         related_name='reservas')
    huesped         = models.ForeignKey(Huesped, on_delete=models.PROTECT,
                                         related_name='reservas')
    tipo_habitacion = models.ForeignKey(TipoHabitacion, on_delete=models.PROTECT,
                                         related_name='reservas')
    habitacion      = models.ForeignKey(Habitacion, on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name='reservas')
    fecha_entrada   = models.DateField()
    fecha_salida    = models.DateField()
    num_adultos     = models.PositiveSmallIntegerField(default=1)
    num_ninos       = models.PositiveSmallIntegerField(default=0)
    estado          = models.CharField(max_length=15, choices=ESTADO, default='PENDIENTE')
    precio_total    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    origen          = models.CharField(max_length=10, choices=ORIGEN, default='DIRECTO')
    observaciones   = models.TextField(blank=True)
    creado_en       = models.DateTimeField(auto_now_add=True)
    creado_por      = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reservas_creadas'
    )

    class Meta:
        verbose_name        = 'Reserva'
        verbose_name_plural = 'Reservas'
        ordering            = ['-creado_en']

    def __str__(self):
        return f"Reserva #{self.pk} — {self.huesped.nombre_completo}"

    @property
    def num_noches(self):
        return (self.fecha_salida - self.fecha_entrada).days

    def clean(self):
        # Validar fechas
        if self.fecha_entrada and self.fecha_salida:
            if self.fecha_entrada >= self.fecha_salida:
                raise ValidationError('La fecha de salida debe ser posterior a la de entrada.')

        # REGLA CRÍTICA: no solapamiento de reservas activas en la misma habitación
        if self.habitacion_id and self.fecha_entrada and self.fecha_salida:
            solapadas = Reserva.objects.filter(
                habitacion=self.habitacion,
                estado__in=['PENDIENTE', 'CONFIRMADA', 'CHECKIN'],
            ).filter(
                Q(fecha_entrada__lt=self.fecha_salida) &
                Q(fecha_salida__gt=self.fecha_entrada)
            ).exclude(pk=self.pk)

            if solapadas.exists():
                raise ValidationError(
                    f'La habitación {self.habitacion} ya tiene una reserva activa en esas fechas.'
                )

    def calcular_precio(self):
        if self.tipo_habitacion_id and self.fecha_entrada and self.fecha_salida:
            precio_noche = Tarifa.get_precio_vigente(
                self.tipo_habitacion, self.fecha_entrada, self.fecha_salida
            )
            self.precio_total = decimal.Decimal(str(precio_noche)) * self.num_noches
        return self.precio_total

    def save(self, *args, **kwargs):
        if not self.precio_total:
            self.calcular_precio()
        super().save(*args, **kwargs)


class Estancia(models.Model):
    ESTADO = [
        ('ACTIVA',     'Activa'),
        ('FINALIZADA', 'Finalizada'),
    ]

    reserva         = models.OneToOneField(Reserva, on_delete=models.CASCADE,
                                            related_name='estancia')
    habitacion      = models.ForeignKey(Habitacion, on_delete=models.PROTECT,
                                         related_name='estancias')
    fecha_checkin   = models.DateTimeField(auto_now_add=True)
    fecha_checkout  = models.DateTimeField(null=True, blank=True)
    precio_final    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado          = models.CharField(max_length=15, choices=ESTADO, default='ACTIVA')
    atendido_por    = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='estancias_atendidas'
    )

    class Meta:
        verbose_name        = 'Estancia'
        verbose_name_plural = 'Estancias'
        ordering            = ['-fecha_checkin']

    def __str__(self):
        return f"Estancia #{self.pk} — Hab. {self.habitacion.numero}"

    @property
    def tiene_deuda(self):
        """REGLA CRÍTICA: no hacer checkout si el folio está pendiente."""
        folio = getattr(self, 'folio', None)
        return folio is None or folio.estado == 'PENDIENTE'

    def calcular_precio_final(self):
        total = self.cargos.aggregate(t=Sum('monto'))['t'] or decimal.Decimal('0')
        self.precio_final = total
        self.save(update_fields=['precio_final'])
        return self.precio_final


class CargoEstancia(models.Model):
    TIPO = [
        ('HABITACION',  'Habitación'),
        ('RESTAURANTE', 'Restaurante'),
        ('LAVANDERIA',  'Lavandería'),
        ('MINIBAR',     'Minibar'),
        ('TELEFONO',    'Teléfono'),
        ('SPA',         'Spa'),
        ('OTRO',        'Otro'),
    ]

    estancia       = models.ForeignKey(Estancia, on_delete=models.CASCADE,
                                        related_name='cargos')
    concepto       = models.CharField(max_length=200)
    monto          = models.DecimalField(max_digits=10, decimal_places=2)
    fecha          = models.DateTimeField(auto_now_add=True)
    tipo           = models.CharField(max_length=15, choices=TIPO, default='OTRO')
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True
    )

    class Meta:
        verbose_name        = 'Cargo'
        verbose_name_plural = 'Cargos'
        ordering            = ['fecha']

    def __str__(self):
        return f"{self.concepto} — S/ {self.monto}"


class Folio(models.Model):
    ESTADO = [
        ('PENDIENTE', 'Pendiente de Pago'),
        ('PAGADO',    'Pagado'),
    ]

    estancia     = models.OneToOneField(Estancia, on_delete=models.CASCADE,
                                         related_name='folio')
    subtotal     = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    igv          = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total        = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado       = models.CharField(max_length=10, choices=ESTADO, default='PENDIENTE')
    fecha_pago   = models.DateTimeField(null=True, blank=True)
    metodo_pago  = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = 'Folio'

    def __str__(self):
        return f"Folio #{self.pk} — S/ {self.total} ({self.get_estado_display()})"

    def recalcular(self):
        igv_rate     = decimal.Decimal(str(getattr(settings, 'IGV', 0.18)))
        self.subtotal = (
            self.estancia.cargos.aggregate(t=Sum('monto'))['t']
            or decimal.Decimal('0')
        )
        self.igv   = (self.subtotal * igv_rate).quantize(decimal.Decimal('0.01'))
        self.total = self.subtotal + self.igv
        self.save()
