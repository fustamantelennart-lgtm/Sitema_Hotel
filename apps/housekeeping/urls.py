from django.urls import path
from . import views

app_name = 'housekeeping'

urlpatterns = [
    path('', views.panel, name='panel'),
]