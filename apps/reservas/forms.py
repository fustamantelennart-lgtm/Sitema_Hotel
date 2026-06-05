from django import forms
from .models import Reserva, CargoEstancia, Huesped


class ReservaForm(forms.ModelForm):
    class Meta:
        model  = Reserva
        fields = [
            'hotel', 'huesped', 'tipo_habitacion',
            'fecha_entrada', 'fecha_salida',
            'num_adultos', 'num_ninos',
            'origen', 'observaciones',
        ]
        widgets = {
            'hotel':           forms.Select(attrs={'class': 'form-select'}),
            'huesped':         forms.Select(attrs={'class': 'form-select'}),
            'tipo_habitacion': forms.Select(attrs={'class': 'form-select'}),
            'fecha_entrada':   forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_salida':    forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'num_adultos':     forms.NumberInput(attrs={'class': 'form-control'}),
            'num_ninos':       forms.NumberInput(attrs={'class': 'form-control'}),
            'origen':          forms.Select(attrs={'class': 'form-select'}),
            'observaciones':   forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class CargoForm(forms.ModelForm):
    class Meta:
        model  = CargoEstancia
        fields = ['concepto', 'monto', 'tipo']
        widgets = {
            'concepto': forms.TextInput(attrs={'class': 'form-control'}),
            'monto':    forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tipo':     forms.Select(attrs={'class': 'form-select'}),
        }