from django.contrib.auth.forms import AuthenticationForm
from .models import CustomUser
from allauth.account.forms import SignupForm
from django import forms
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserCreationForm(SignupForm):
    email = forms.EmailField(required=True, label="Email")
    phone_number = forms.CharField(max_length=20, required=False, label="Номер телефона")
    country = forms.CharField(max_length=60, required=False, label="Страна")
    avatar = forms.ImageField(required=False, label="Аватар")

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.save()
        return user

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number and not phone_number.isdigit():
            raise forms.ValidationError("Номер телефона должен состоять только из цифр")
        return phone_number

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует")
        return email

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="Email",
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваш email',
            'autocomplete': 'email'
        })
    )

class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="Новый пароль",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите новый пароль',
            'autocomplete': 'new-password'
        }),
        help_text="Пароль должен содержать не менее 8 символов."
    )
    new_password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Повторите новый пароль',
            'autocomplete': 'new-password'
        })
    )

class CustomAuthenticationForm(AuthenticationForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'password1']