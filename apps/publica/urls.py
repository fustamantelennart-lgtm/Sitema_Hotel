from django.urls import path
from . import views

app_name = 'publica'

urlpatterns = [
    path('',                        views.inicio,        name='inicio'),
    path('reservar/',               views.reservar,      name='reservar'),
    path('pago/<int:pk>/',          views.pago,          name='pago'),
    path('procesar-pago/<int:pk>/', views.procesar_pago, name='procesar_pago'),
    path('habitacion/<int:pk>/',    views.detalle,       name='detalle'),
    path('confirmacion/<int:pk>/',  views.confirmacion,  name='confirmacion'),
    path('consultar-dni/',          views.consultar_dni, name='consultar_dni'),
]