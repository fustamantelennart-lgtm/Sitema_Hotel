from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import TareaLimpieza


@login_required
def panel(request):
    tareas = TareaLimpieza.objects.filter(
        estado__in=['PENDIENTE', 'EN_PROCESO']
    ).select_related('habitacion', 'asignada_a')
    return render(request, 'housekeeping/panel.html', {'tareas': tareas})