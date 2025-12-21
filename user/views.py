from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.contrib.auth import login
from django.contrib import messages
from .forms import CustomPasswordResetForm, CustomSetPasswordForm, CustomUserCreationForm
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.core.cache import cache


class RegisterView(CreateView):
    template_name = "user/register.html"
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('mailing:home')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)

        # Очищаем кеш пользователя после регистрации
        if user.id:
            cache_key = f"user_stats_{user.id}"
            cache.delete(cache_key)

        return super().form_valid(form)


class CustomPasswordResetView(PasswordResetView):
    template_name = 'user/password_reset.html'
    form_class = CustomPasswordResetForm
    email_template_name = 'user/password_reset_email.html'
    subject_template_name = 'user/password_reset_subject.txt'
    success_url = reverse_lazy('user:password_reset_done')

    def form_valid(self, form):
        messages.info(self.request, 'Инструкции по восстановлению пароля отправлены на ваш email.')
        return super().form_valid(form)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'user/password_reset_done.html'

    @method_decorator(cache_page(60 * 5))  # Кешируем страницу на 5 минут
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'user/password_reset_confirm.html'
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy('user:password_reset_complete')

    def form_valid(self, form):
        messages.success(self.request, 'Пароль успешно изменен! Теперь вы можете войти с новым паролем.')
        return super().form_valid(form)


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'user/password_reset_complete.html'

    @method_decorator(cache_page(60 * 5))  # Кешируем страницу на 5 минут
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

