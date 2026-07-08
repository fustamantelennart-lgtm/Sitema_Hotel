from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('login/',  views.login_view,  name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/ajax/', views.registro_cliente_ajax, name='registro_ajax'),
]