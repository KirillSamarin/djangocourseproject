from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.contrib import messages
from .forms import CustomPasswordResetForm, CustomSetPasswordForm, CustomUserChangeForm
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from .models import CustomUser


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'user/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context.update({
            'user': user,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'avatar': user.avatar,
            'phone_number': user.phone_number,
            'country': user.country
        })
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = CustomUserChangeForm  # Используем форму для изменения
    template_name = 'user/profile_update.html'
    success_url = reverse_lazy('user:profile')

    def get_object(self, queryset=None):
        # Возвращаем текущего авторизованного пользователя
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Профиль успешно обновлен!')
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
