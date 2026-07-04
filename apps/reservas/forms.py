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
                'class': 'form-select',
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


class ReservaPresencialForm(forms.Form):
    """Form para reserva presencial — crea huésped automáticamente."""
    # Datos huésped
    tipo_doc    = forms.ChoiceField(
        choices=Huesped.TIPO_DOC,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='DNI'
    )
    num_doc     = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 75897100',
            'id': 'id_num_doc',
            'maxlength': '8',
        })
    )
    nombres     = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_nombres',
            'placeholder': 'Se autocompleta con DNI',
        })
    )
    apellidos   = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_apellidos',
            'placeholder': 'Se autocompleta con DNI',
        })
    )
    email       = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'opcional'})
    )
    telefono    = forms.CharField(
        max_length=15, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'opcional'})
    )

    # Datos reserva
    tipo_habitacion = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_habitacion'})
    )
    fecha_entrada   = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    fecha_salida    = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    num_adultos     = forms.IntegerField(
        min_value=1, initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    num_ninos       = forms.IntegerField(
        min_value=0, initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    observaciones   = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )

    def __init__(self, *args, **kwargs):
        from apps.recepcion.models import TipoHabitacion
        super().__init__(*args, **kwargs)
        self.fields['tipo_habitacion'].queryset = TipoHabitacion.objects.all()

    def clean_num_doc(self):
        num_doc = self.cleaned_data.get('num_doc', '').strip()
        tipo    = self.cleaned_data.get('tipo_doc', 'DNI')
        if tipo == 'DNI' and (not num_doc.isdigit() or len(num_doc) != 8):
            raise forms.ValidationError('El DNI debe tener 8 dígitos.')
        return num_doc

    def clean(self):
        cleaned = super().clean()
        fe = cleaned.get('fecha_entrada')
        fs = cleaned.get('fecha_salida')
        if fe and fs and fs <= fe:
            raise forms.ValidationError('La fecha de salida debe ser posterior a la entrada.')
        return cleaned

    def get_or_create_huesped(self):
        """Crea o recupera el huésped con los datos del form."""
        num_doc = self.cleaned_data['num_doc']
        huesped, created = Huesped.objects.get_or_create(
            num_doc=num_doc,
            defaults={
                'tipo_doc':   self.cleaned_data['tipo_doc'],
                'nombres':    self.cleaned_data['nombres'],
                'apellidos':  self.cleaned_data['apellidos'],
                'email':      self.cleaned_data.get('email', ''),
                'telefono':   self.cleaned_data.get('telefono', ''),
                'nacionalidad': 'Peruana',
            }
        )
        return huesped, created
    def __init__(self, *args, **kwargs):
        from apps.recepcion.models import TipoHabitacion
        super().__init__(*args, **kwargs)
        tipos = TipoHabitacion.objects.all()
        self.fields['tipo_habitacion'].queryset = tipos
        # Agregar data-precio a cada opción
        self.fields['tipo_habitacion'].widget = forms.Select(
            attrs={'class': 'form-select', 'id': 'id_tipo_habitacion'},
            choices=[('', '---------')] + [
                (t.pk, t.nombre) for t in tipos
            ]
        )
        # Guardar precios para el template
        self.tipo_precios = {str(t.pk): str(t.precio_base) for t in tipos}


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