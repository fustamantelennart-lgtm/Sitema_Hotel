from .models import Hotel, TipoHabitacion, Habitacion, ImagenTipoHabitacion
from django.contrib import admin


class ImagenInline(admin.TabularInline):
    model  = ImagenTipoHabitacion
    extra  = 3
    fields = ['imagen', 'orden', 'caption']


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ruc', 'estrellas', 'telefono')


@admin.register(TipoHabitacion)
class TipoHabitacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'hotel', 'capacidad', 'precio_base')
    inlines      = [ImagenInline]


@admin.register(Habitacion)
class HabitacionAdmin(admin.ModelAdmin):
    list_display  = ('numero', 'piso', 'tipo', 'estado', 'hotel')
    list_filter   = ('estado', 'piso', 'tipo', 'hotel')
    list_editable = ('estado',)
    ordering      = ('piso', 'numero')


@admin.register(ImagenTipoHabitacion)
class ImagenTipoHabitacionAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'orden', 'caption')