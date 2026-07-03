from django.urls import path
from . import views

app_name = 'cuenta'

urlpatterns = [
    path('registro/',                   views.registro_cliente, name='registro'),
    path('login/',                      views.login_cliente,    name='login'),
    path('logout/',                     views.logout_cliente,   name='logout'),
    path('perfil/',                     views.perfil_cliente,   name='perfil'),
    path('reservas/<int:pk>/cancelar/', views.cancelar_reserva, name='cancelar_reserva'),
]