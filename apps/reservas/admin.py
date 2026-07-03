from django.contrib import admin
from .models import Huesped, Tarifa, Reserva, Estancia, CargoEstancia, Folio


@admin.register(Huesped)
class HuespedAdmin(admin.ModelAdmin):
    list_display  = ('apellidos', 'nombres', 'tipo_doc', 'num_doc', 'nacionalidad')
    search_fields = ('nombres', 'apellidos', 'num_doc')


@admin.register(Tarifa)
class TarifaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo_habitacion', 'precio_noche', 'fecha_inicio', 'fecha_fin', 'activa')
    list_filter  = ('activa', 'tipo_habitacion')


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display  = ('pk', 'huesped', 'tipo_habitacion', 'habitacion', 'fecha_entrada', 'fecha_salida', 'estado')
    list_filter   = ('estado', 'hotel')
    search_fields = ('huesped__nombres', 'huesped__apellidos', 'huesped__num_doc')
    list_editable = ('estado',)


@admin.register(Estancia)
class EstanciaAdmin(admin.ModelAdmin):
    list_display = ('pk', 'reserva', 'habitacion', 'fecha_checkin', 'estado')
    list_filter  = ('estado',)


@admin.register(CargoEstancia)
class CargoEstanciaAdmin(admin.ModelAdmin):
    list_display = ('concepto', 'monto', 'tipo', 'estancia', 'fecha')
    list_filter  = ('tipo',)


@admin.register(Folio)
class FolioAdmin(admin.ModelAdmin):
    list_display = ('pk', 'estancia', 'subtotal', 'igv', 'total', 'estado')
    list_filter  = ('estado',)