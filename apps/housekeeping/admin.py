from django.contrib import admin
from .models import TareaLimpieza, IncidenteHabitacion


@admin.register(TareaLimpieza)
class TareaLimpiezaAdmin(admin.ModelAdmin):
    list_display  = ('habitacion', 'estado', 'prioridad', 'asignada_a', 'fecha_creacion')
    list_filter   = ('estado', 'prioridad')
    list_editable = ('estado',)


@admin.register(IncidenteHabitacion)
class IncidenteAdmin(admin.ModelAdmin):
    list_display = ('habitacion', 'tipo', 'descripcion', 'resuelto', 'fecha')
    list_filter  = ('tipo', 'resuelto')