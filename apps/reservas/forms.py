from django import forms
from .models import Reserva, CargoEstancia, Huesped
from apps.recepcion.models import Hotel


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
            'huesped':         forms.Select(attrs={
                'class': 'form-select select2-huesped',
                'data-placeholder': 'Buscar por nombre o DNI...',
            }),
            'tipo_habitacion': forms.Select(attrs={'class': 'form-select'}),
            'fecha_entrada':   forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_salida':    forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'num_adultos':     forms.NumberInput(attrs={'class': 'form-control'}),
            'num_ninos':       forms.NumberInput(attrs={'class': 'form-control'}),
            'origen':          forms.HiddenInput(),
            'observaciones':   forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        hotel = Hotel.objects.first()
        if hotel:
            self.fields['hotel'].initial  = hotel.pk
            self.fields['hotel'].queryset = Hotel.objects.all()
            self.fields['hotel'].widget   = forms.HiddenInput()
        self.fields['origen'].initial = 'DIRECTO'


class CargoForm(forms.ModelForm):
    class Meta:
        model  = CargoEstancia
        fields = ['concepto', 'monto', 'tipo']
        widgets = {
            'concepto': forms.TextInput(attrs={'class': 'form-control'}),
            'monto':    forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tipo':     forms.Select(attrs={'class': 'form-select'}),
        }


class HuespedForm(forms.ModelForm):
    class Meta:
        model  = Huesped
        fields = ['tipo_doc', 'num_doc', 'nombres', 'apellidos',
                  'email', 'telefono', 'nacionalidad']
        widgets = {
            'tipo_doc':     forms.Select(attrs={'class': 'form-select'}),
            'num_doc':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 12345678'}),
            'nombres':      forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos':    forms.TextInput(attrs={'class': 'form-control'}),
            'email':        forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono':     forms.TextInput(attrs={'class': 'form-control'}),
            'nacionalidad': forms.TextInput(attrs={'class': 'form-control'}),
        }