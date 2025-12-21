from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class OwnerOrManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Миксин для проверки владельца или менеджера"""

    def test_func(self):
        user = self.request.user
        obj = self.get_object()

        # Проверяем группы
        is_manager = user.groups.filter(name='Менеджеры').exists()

        # Доступ если: владелец объекта ИЛИ менеджер
        return obj.owner == user or is_manager

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("У вас нет прав для выполнения этого действия")
        return super().handle_no_permission()


def user_is_manager(user):
    """Проверяет, является ли пользователь менеджером"""
    return user.groups.filter(name='Менеджеры').exists()


def user_is_owner_or_manager(user, obj):
    """Проверяет, является ли пользователь владельцем или менеджером"""
    if not user.is_authenticated:
        return False
    return obj.owner == user or user_is_manager(user)