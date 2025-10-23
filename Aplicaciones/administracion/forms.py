from django import forms
from django.contrib.auth.hashers import check_password
from Aplicaciones.padron.models import CredencialUsuario

class LoginForm(forms.Form):
    cedula = forms.CharField(
        label='Cédula',
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su cédula',
            'required': True
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su contraseña',
            'required': True
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        cedula = cleaned_data.get('cedula')
        password = cleaned_data.get('password')

        if cedula and password:
            try:
                credencial = CredencialUsuario.objects.get(
                    usuario=cedula,
                    estado='activo'
                )
                if not credencial.verificar_contrasena(password):
                    raise forms.ValidationError("Cédula o contraseña incorrectos")
                
                # Verificar si el usuario ya votó
                if hasattr(credencial.padron, 'voto') and credencial.padron.voto:
                    raise forms.ValidationError("Usted ya ha emitido su voto")
                
                cleaned_data['credencial'] = credencial
                
            except CredencialUsuario.DoesNotExist:
                raise forms.ValidationError("Cédula o contraseña incorrectos")
        
        return cleaned_data
