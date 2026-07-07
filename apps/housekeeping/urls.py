from django.urls import path
from . import views

app_name = 'housekeeping'

urlpatterns = [
    path('',                        views.panel,              name='panel'),
    path('<int:pk>/iniciar/',       views.iniciar,            name='iniciar'),
    path('<int:pk>/completar/',     views.completar,          name='completar'),
    path('<int:pk>/asignar/',       views.asignar,            name='asignar'),
    path('historial/',              views.historial,           name='historial'),
    path('incidentes/',             views.incidentes,          name='incidentes'),
    path('incidentes/reportar/',    views.reportar_incidente,  name='reportar_incidente'),
    path('incidentes/<int:pk>/resolver/', views.resolver_incidente, name='resolver_incidente'),
]