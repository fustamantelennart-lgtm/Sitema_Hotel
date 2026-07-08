from django.urls import path
from . import views

app_name = 'recepcion'

urlpatterns = [
    path('',                              views.dashboard,          name='dashboard'),
    path('habitaciones/',                 views.habitaciones,       name='habitaciones'),
    path('habitaciones/<int:pk>/estado/', views.cambiar_estado,     name='cambiar_estado'),
    path('habitaciones/nueva/',           views.nueva_habitacion,   name='nueva_habitacion'),
]