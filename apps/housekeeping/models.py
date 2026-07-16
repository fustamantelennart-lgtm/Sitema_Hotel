from django.db import models
from django.conf import settings
from apps.recepcion.models import Habitacion
from utils.models import ModeloBase


class TareaLimpieza(ModeloBase):
    ESTADO = [
        ('PENDIENTE',  'Pendiente'),
        ('EN_PROCESO', 'En Proceso'),
        ('LISTA',      'Lista'),
    ]
    PRIORIDAD = [
        ('ALTA',  'Alta'),
        ('MEDIA', 'Media'),
        ('BAJA',  'Baja'),
    ]
    TIPO = [
        ('LIMPIEZA', 'Limpieza'),
        ('REVISION', 'Revisión pre-checkout'),
    ]
    habitacion       = models.ForeignKey(Habitacion, on_delete=models.CASCADE,
                                         related_name='tareas_limpieza')
    tipo             = models.CharField(max_length=10, choices=TIPO, default='LIMPIEZA')
    estancia_relacionada = models.ForeignKey(
        'reservas.Estancia', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tareas_housekeeping'
    )
    asignada_a       = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tareas_asignadas'
    )
    estado           = models.CharField(max_length=15, choices=ESTADO, default='PENDIENTE')
    prioridad        = models.CharField(max_length=5,  choices=PRIORIDAD, default='MEDIA')
    fecha_creacion   = models.DateTimeField(auto_now_add=True)
    fecha_completada = models.DateTimeField(null=True, blank=True)
    observaciones    = models.TextField(blank=True)

    class Meta:
        verbose_name        = 'Tarea de Limpieza'
        verbose_name_plural = 'Tareas de Limpieza'
        ordering            = ['habitacion__piso', 'habitacion__numero']

    def __str__(self):
        return f"Limpieza Hab. {self.habitacion.numero} — {self.get_estado_display()}"

    def marcar_lista(self):
        from django.utils import timezone
        self.estado           = 'LISTA'
        self.fecha_completada = timezone.now()
        self.save()
        
        if self.habitacion.estado == 'LIMPIEZA':
            self.habitacion.estado = 'DISPONIBLE'
            self.habitacion.save()


class IncidenteHabitacion(ModeloBase):
    TIPO = [
        ('DESPERFECTO', 'Desperfecto'),
        ('MINIBAR',     'Consumo Minibar'),
        ('LIMPIEZA',    'Limpieza Especial'),
        ('OTRO',        'Otro'),
    ]

    habitacion    = models.ForeignKey(Habitacion, on_delete=models.CASCADE,
                                      related_name='incidentes')
    tipo          = models.CharField(max_length=15, choices=TIPO)
    descripcion   = models.TextField()
    monto_cobrar  = models.DecimalField(max_digits=10, decimal_places=2,
                                        null=True, blank=True)
    reportado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    fecha    = models.DateTimeField(auto_now_add=True)
    resuelto = models.BooleanField(default=False)

    class Meta:
        verbose_name        = 'Incidente'
        verbose_name_plural = 'Incidentes'
        ordering            = ['-fecha']

    def __str__(self):
        return f"{self.get_tipo_display()} — Hab. {self.habitacion.numero}"