from django.urls import path
from . import views

app_name = 'gerencia'

urlpatterns = [
    path('',              views.dashboard,      name='dashboard'),
    path('ocupacion/',    views.ocupacion,       name='ocupacion'),
    path('usuarios/',     views.usuarios,        name='usuarios'),
    path('reportes/',     views.reportes,        name='reportes'),
    path('exportar/excel/', views.exportar_excel, name='exportar_excel'),
    path('exportar/pdf/',   views.exportar_pdf,   name='exportar_pdf'),
]