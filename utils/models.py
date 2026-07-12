from django.db import models
from django.conf import settings
from django.utils import timezone


class ModeloBase(models.Model):
    creado_en      = models.DateTimeField(default=timezone.now, verbose_name='Creado en',      db_index=True)
    actualizado_en = models.DateTimeField(default=timezone.now, verbose_name='Actualizado en')
    activo         = models.BooleanField(default=True,          verbose_name='Activo',         db_index=True)
    creado_por     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name='Creado por'
    )

    def save(self, *args, **kwargs):
        self.actualizado_en = timezone.now()
        super().save(*args, **kwargs)

    def eliminar(self, usuario=None):
        self.activo = False
        if usuario:
            self.creado_por = usuario
        self.save(update_fields=['activo', 'actualizado_en'])

    def restaurar(self):
        self.activo = True
        self.save(update_fields=['activo', 'actualizado_en'])

    class Meta:
        abstract = True