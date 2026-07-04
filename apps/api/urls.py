from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from . import views

router = DefaultRouter()
router.register(r'hoteles',          views.HotelViewSet,          basename='hotel')
router.register(r'tipos-habitacion', views.TipoHabitacionViewSet, basename='tipo-habitacion')
router.register(r'habitaciones',     views.HabitacionViewSet,     basename='habitacion')
router.register(r'huespedes',        views.HuespedViewSet,        basename='huesped')
router.register(r'reservas',         views.ReservaViewSet,        basename='reserva')

urlpatterns = [
    path('',        include(router.urls)),
    path('token/',  obtain_auth_token,        name='api-token'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/',   SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/',  SpectacularRedocView.as_view(url_name='schema'),   name='redoc'),
]