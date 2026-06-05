from django.urls import path
from . import views

app_name = 'recepcion'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
]