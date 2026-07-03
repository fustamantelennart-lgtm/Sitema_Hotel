from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from .models import Usuario


class RegistroClienteForm(UserCreationForm):
    email      = forms.EmailField(required=True, label='Correo electrónico')
    first_name = forms.CharField(max_length=50, required=False, label='Nombres')
    last_name  = forms.CharField(max_length=50, required=False, label='Apellidos')
    telefono   = forms.CharField(max_length=15, required=False, label='Teléfono (opcional)')
    num_doc    = forms.CharField(max_length=8, required=True, label='DNI')

    class Meta:
        model  = Usuario
        fields = ('email', 'first_name', 'last_name', 'telefono',
                  'num_doc', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo.')
        return email

    def clean_num_doc(self):
        num_doc = self.cleaned_data.get('num_doc', '').strip()
        if not num_doc.isdigit() or len(num_doc) != 8:
            raise forms.ValidationError('El DNI debe tener exactamente 8 dígitos.')
        return num_doc

    def save(self, commit=True):
        user            = super().save(commit=False)
        user.email      = self.cleaned_data['email']
        user.username   = self.cleaned_data['email']
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name  = self.cleaned_data.get('last_name', '')
        user.rol        = 'cliente'
        user.telefono   = self.cleaned_data.get('telefono', '')
        if commit:
            user.save()
            self._vincular_huesped(user)
        return user

    def _vincular_huesped(self, user):
        from apps.reservas.models import Huesped
        num_doc = self.cleaned_data['num_doc']
        huesped = Huesped.objects.filter(num_doc=num_doc).first()
        if huesped:
            huesped.usuario   = user
            huesped.email     = user.email
            huesped.telefono  = user.telefono or huesped.telefono
            huesped.nombres   = user.first_name or huesped.nombres
            huesped.apellidos = user.last_name  or huesped.apellidos
            huesped.save()
        else:
            Huesped.objects.create(
                num_doc   = num_doc,
                tipo_doc  = 'DNI',
                nombres   = user.first_name,
                apellidos = user.last_name,
                email     = user.email,
                telefono  = user.telefono,
                usuario   = user,
            )


class LoginClienteForm(AuthenticationForm):
    username = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'placeholder': 'tucorreo@ejemplo.com'})
    )
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput)

    def clean(self):
        email    = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        if email and password:
            try:
                user = Usuario.objects.get(email=email, rol='cliente')
                self.user_cache = authenticate(
                    self.request,
                    username=user.username,
                    password=password
                )
                if self.user_cache is None:
                    raise forms.ValidationError('Correo o contraseña incorrectos.')
            except Usuario.DoesNotExist:
                raise forms.ValidationError('No existe una cuenta con ese correo.')
        return self.cleaned_data