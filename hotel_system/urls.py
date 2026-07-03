from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('recepcion:dashboard'), name='home'),
    path('recepcion/',    include('apps.recepcion.urls',       namespace='recepcion')),
    path('reservas/',     include('apps.reservas.urls',        namespace='reservas')),
    path('housekeeping/', include('apps.housekeeping.urls',    namespace='housekeeping')),
    path('gerencia/',     include('apps.gerencia.urls',        namespace='gerencia')),
    path('usuarios/',     include('apps.usuarios.urls',        namespace='usuarios')),
    path('web/',          include('apps.publica.urls',         namespace='publica')),
    path('cuenta/',       include('apps.usuarios.urls_cuenta', namespace='cuenta')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)