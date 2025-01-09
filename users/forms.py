from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm


class LoginUserForm(AuthenticationForm):
    error_messages = {
        'invalid_login': (
            "Не правильний пароль або ім'я користувача"
        ),
        'inactive': ("This account is inactive."),
    }

    username = forms.CharField(label='Логін',
                               widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Username'}))
    password = forms.CharField(label='Пароль',
                               widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'pass'}))

    class Meta:
        model = get_user_model()
        fields = ('username', 'password')


class RegisterUserForm(forms.ModelForm):
    username = forms.CharField(label='Логін',
                               widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Username'}))
    password = forms.CharField(label='Пароль',
                               widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'pass'}))
    password2 = forms.CharField(label='Повторіть пароль',
                                widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'pass'}))

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'first_name', 'last_name', 'password', 'password2')
        labels = {
            'email': 'E-mail',
            'first_name': "І'мя",
            'last_name': "Фамілія"
        }

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Паролі не співпадають!')
        return cd['password']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if get_user_model().objects.filter(email=email).exists():
            raise forms.ValidationError('Такий E-mail вже існує')
        return email