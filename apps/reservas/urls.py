from django.urls import path
from . import views

app_name = 'reservas'

urlpatterns = [
    path('',                    views.lista,       name='lista'),
    path('nueva/',              views.nueva,       name='nueva'),
    path('<int:pk>/checkin/',   views.checkin,     name='checkin'),
    path('<int:pk>/checkout/',  views.checkout,    name='checkout'),
    path('<int:pk>/folio/',     views.folio,       name='folio'),
    path('<int:pk>/cargo/',     views.agregar_cargo, name='cargo'),
]