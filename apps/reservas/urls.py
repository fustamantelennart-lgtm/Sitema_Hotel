from django.urls import path
from . import views

app_name = 'reservas'

urlpatterns = [
    path('',                                views.lista,               name='lista'),
    path('nueva/',                          views.nueva,               name='nueva'),
    path('huespedes/',                      views.huespedes,           name='huespedes'),
    path('huespedes/<int:pk>/',             views.huesped_detalle,     name='huesped_detalle'),
    path('checkin/',                        views.checkin_lista,       name='checkin_lista'),
    path('checkin/buscar/',                 views.checkin_buscar,      name='checkin_buscar'),
    path('checkout/',                       views.checkout_lista,      name='checkout_lista'),
    path('disponibilidad/',                 views.disponibilidad,      name='disponibilidad'),
    path('solicitudes-web/',                views.solicitudes_web,     name='solicitudes_web'),
    path('<int:pk>/checkin/',               views.checkin,             name='checkin'),
    path('<int:pk>/checkout/',              views.checkout,            name='checkout'),
    path('<int:pk>/folio/',                 views.folio,               name='folio'),
    path('<int:pk>/cargo/',                 views.agregar_cargo,       name='cargo'),
    path('<int:pk>/pagar/',                 views.pagar_folio,         name='pagar_folio'),
    path('<int:pk>/cancelar/',              views.cancelar,            name='cancelar'),
    path('<int:pk>/solicitar-revision/',    views.solicitar_revision,  name='solicitar_revision'),
    path('<int:pk>/confirmar-web/',         views.confirmar_solicitud, name='confirmar_solicitud'),
    path('<int:pk>/rechazar-web/',          views.rechazar_solicitud,  name='rechazar_solicitud'),
    path('<int:pk>/cambiar-habitacion/',    views.cambiar_habitacion,  name='cambiar_habitacion'),
]