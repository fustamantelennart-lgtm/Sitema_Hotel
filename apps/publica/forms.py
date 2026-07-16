from django import forms
from apps.reservas.models import Huesped
from apps.recepcion.models import TipoHabitacion, Hotel, OpcionCheckin


class ReservaPublicaForm(forms.Form):
    # Datos del huésped
    tipo_doc = forms.ChoiceField(
        choices=[('DNI', 'DNI'), ('PASAPORTE', 'Pasaporte'), ('CE', 'Carnet de Extranjería')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    num_doc = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 12345678',
        })
    )
    nombres = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    apellidos = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        })
    )
    telefono = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 999888777'
        })
    )
    nacionalidad = forms.CharField(
        max_length=60,
        initial='Peruana',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    # Datos de la reserva
    tipo_habitacion = forms.ModelChoiceField(
        queryset=TipoHabitacion.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    fecha_entrada = forms.DateField(
        widget=forms.DateInput(
        attrs={'class': 'form-control', 'type': 'date'},
        format='%Y-%m-%d'
    )
    )
    fecha_salida = forms.DateField(
            widget=forms.DateInput(
        attrs={'class': 'form-control', 'type': 'date'},
        format='%Y-%m-%d'
    ))
    num_adultos = forms.IntegerField(
        min_value=1, max_value=10, initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    num_ninos = forms.IntegerField(
        min_value=0, max_value=10, initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
    opcion_checkin = forms.ModelChoiceField(
        queryset=OpcionCheckin.objects.none(),
        required=False,
        empty_label=None,
        widget=forms.RadioSelect(),
        label='Hora de check-in'
    )
    opcion_checkout = forms.ModelChoiceField(
        queryset=OpcionCheckin.objects.none(),
        required=False,
        empty_label=None,
        widget=forms.RadioSelect(),
        label='Hora de check-out'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregar data-precio a cada opción del tipo de habitación
        choices = [('', '---------')]
        for tipo in TipoHabitacion.objects.all():
            choices.append((tipo.pk, tipo.nombre))
        self.fields['tipo_habitacion'].choices = choices
        # Guardar precios para usar en el widget
        self.tipos_precios = {
            str(tipo.pk): str(tipo.precio_base)
            for tipo in TipoHabitacion.objects.all()
        }
        hotel = Hotel.objects.first()
        if hotel:
            self.fields['opcion_checkin'].queryset = OpcionCheckin.objects.filter(
                hotel=hotel, tipo='CHECKIN', activo=True
            )
            self.fields['opcion_checkout'].queryset = OpcionCheckin.objects.filter(
                hotel=hotel, tipo='CHECKOUT', activo=True
            )
            # Seleccionar opción estándar por defecto
            checkin_std = OpcionCheckin.objects.filter(
                hotel=hotel, tipo='CHECKIN', cargo_extra=0
            ).first()
            checkout_std = OpcionCheckin.objects.filter(
                hotel=hotel, tipo='CHECKOUT', cargo_extra=0
            ).first()
            if checkin_std:
                self.fields['opcion_checkin'].initial = checkin_std
            if checkout_std:
                self.fields['opcion_checkout'].initial = checkout_std

    def clean_num_doc(self):
        tipo = self.cleaned_data.get('tipo_doc')
        num  = self.cleaned_data.get('num_doc', '')
        if tipo == 'DNI' and (not num.isdigit() or len(num) != 8):
            raise forms.ValidationError('El DNI debe tener exactamente 8 dígitos numéricos.')
        return num

    def clean(self):
        cleaned = super().clean()
        fe      = cleaned.get('fecha_entrada')
        fs      = cleaned.get('fecha_salida')
        num_doc = cleaned.get('num_doc')

        if fe and fs:
            from datetime import date
            if fe < date.today():
                raise forms.ValidationError('La fecha de entrada no puede ser en el pasado.')
            if fe >= fs:
                raise forms.ValidationError('La fecha de salida debe ser posterior a la entrada.')

        # REGLA: mismo DNI no puede tener más de 1 reserva PENDIENTE
        if num_doc:
            from apps.reservas.models import Reserva, Huesped
            try:
                huesped    = Huesped.objects.get(num_doc=num_doc)
                pendientes = Reserva.objects.filter(
                    huesped=huesped,
                    estado='PENDIENTE',
                    origen='WEB'
                ).count()
                if pendientes >= 1:
                    raise forms.ValidationError(
                        'Ya tienes una solicitud pendiente de confirmación. '
                        'Espera a que el hotel la procese antes de hacer otra.'
                    )
            except Huesped.DoesNotExist:
                pass

        return cleaned