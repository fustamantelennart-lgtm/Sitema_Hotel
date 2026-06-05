from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    return render(request, 'gerencia/dashboard.html')


@login_required
def ocupacion(request):
    return render(request, 'gerencia/ocupacion.html')


@login_required
def usuarios(request):
    return render(request, 'gerencia/usuarios.html')