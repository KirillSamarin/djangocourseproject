from django.views.generic import DetailView, CreateView, DeleteView, TemplateView
from mailing.forms import ReceiverForm, MessageForm, MailingForm
from mailing.models import ReceiverMailing, Message
from mailing.permissions import OwnerOrManagerRequiredMixin, user_is_manager
from django.views.generic import ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from user.models import CustomUser
from mailing.models import Mailing
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.core.cache import cache
from django.db.models import Count, Q


# Общие View
class Home(LoginRequiredMixin, TemplateView):
    template_name = 'mailing/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated:
            # Используем кеширование для статистики пользователя
            cache_key = f"user_home_stats_{user.id}"
            cached_stats = cache.get(cache_key)

            if cached_stats:
                context.update(cached_stats)
            else:
                # Пользователь видит только свои данные
                mailing_count = Mailing.objects.filter(owner=user).count()
                mailing_active_count = Mailing.objects.filter(status='Запущена', owner=user).count()

                # Количество уникальных получателей у пользователя
                user_mailings = Mailing.objects.filter(owner=user)
                receivers_set = set()
                for mailing in user_mailings:
                    receivers_set.update(mailing.receivers.all())
                receivers_count = len(receivers_set)

                successful_mailings = user.successful_mailing_count or 0
                unsuccessful_mailings = user.unsuccessful_mailing_count or 0
                messages_count = user.messages_count or 0

                # Сохраняем в кеш на 2 минуты
                stats = {
                    'mailing_count': mailing_count,
                    'mailing_active_count': mailing_active_count,
                    'receivers_count': receivers_count,
                    'successful_mailings': successful_mailings,
                    'unsuccessful_mailings': unsuccessful_mailings,
                    'messages_count': messages_count,
                }
                cache.set(cache_key, stats, 120)  # 120 секунд = 2 минуты
                context.update(stats)

        return context


# Получатели - упрощенная версия
class ReceiverDetail(LoginRequiredMixin, DetailView):
    model = ReceiverMailing
    template_name = 'mailing/receiver.html'
    context_object_name = 'receiver'

    @method_decorator(cache_page(60 * 3))  # Кешируем страницу на 3 минуты
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        receiver = super().get_object(queryset)
        user = self.request.user

        if user_is_manager(user):
            return receiver

        # Проверяем, есть ли у пользователя рассылки с этим получателем
        if Mailing.objects.filter(owner=user, receivers=receiver).exists():
            return receiver

        raise PermissionDenied("Вы не можете просматривать этого получателя")


class ReceiverCreateView(LoginRequiredMixin, CreateView):
    model = ReceiverMailing
    form_class = ReceiverForm
    template_name = 'mailing/receiver_form.html'
    success_url = reverse_lazy('mailing:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Очищаем кеш после создания получателя
        cache.delete_pattern('*user_home_stats_*')
        return response


class ReceiverUpdateView(LoginRequiredMixin, UpdateView):
    model = ReceiverMailing
    form_class = ReceiverForm
    template_name = 'mailing/receiver_edit.html'
    success_url = reverse_lazy('mailing:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Очищаем кеш после обновления получателя
        cache.delete_pattern('*user_home_stats_*')
        return response

    def dispatch(self, request, *args, **kwargs):
        # Проверяем права
        receiver = self.get_object()
        user = request.user

        # Получатели не привязаны к владельцам, поэтому:
        # 1. Менеджеры могут редактировать всех
        # 2. Обычные пользователи могут редактировать только если они создали рассылку с этим получателем
        if user_is_manager(user):
            return super().dispatch(request, *args, **kwargs)

        # Проверяем, есть ли у пользователя рассылки с этим получателем
        if Mailing.objects.filter(owner=user, receivers=receiver).exists():
            return super().dispatch(request, *args, **kwargs)

        raise PermissionDenied("Вы не можете редактировать этого получателя")


class ReceiverDeleteView(LoginRequiredMixin, DeleteView):
    model = ReceiverMailing
    template_name = 'mailing/receiver_delete.html'
    success_url = reverse_lazy('mailing:home')

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        # Очищаем кеш после удаления получателя
        cache.delete_pattern('*user_home_stats_*')
        return response

    def dispatch(self, request, *args, **kwargs):
        # Аналогичная проверка как в UpdateView
        receiver = self.get_object()
        user = request.user

        if user_is_manager(user):
            return super().dispatch(request, *args, **kwargs)

        if Mailing.objects.filter(owner=user, receivers=receiver).exists():
            return super().dispatch(request, *args, **kwargs)

        raise PermissionDenied("Вы не можете удалить этого получателя")


# Сообщения - упрощенная версия
class MessageDetail(LoginRequiredMixin, DetailView):
    model = Message
    template_name = 'mailing/message.html'
    context_object_name = 'message'

    @method_decorator(cache_page(60 * 3))  # Кешируем страницу на 3 минуты
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        message = super().get_object(queryset)
        user = self.request.user

        if user_is_manager(user):
            return message

        # Проверяем, использует ли пользователь это сообщение в своих рассылках
        if Mailing.objects.filter(owner=user, message=message).exists():
            return message

        raise PermissionDenied("Вы не можете просматривать это сообщение")


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'mailing/message_form.html'
    success_url = reverse_lazy('mailing:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Очищаем кеш после создания сообщения
        cache.delete_pattern('*user_home_stats_*')
        return response


class MessageUpdateView(LoginRequiredMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = 'mailing/message_edit.html'
    success_url = reverse_lazy('mailing:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Очищаем кеш после обновления сообщения
        cache.delete_pattern('*user_home_stats_*')
        return response

    def dispatch(self, request, *args, **kwargs):
        message = self.get_object()
        user = request.user

        if user_is_manager(user):
            return super().dispatch(request, *args, **kwargs)

        # Проверяем, использует ли пользователь это сообщение в своих рассылках
        if Mailing.objects.filter(owner=user, message=message).exists():
            return super().dispatch(request, *args, **kwargs)

        raise PermissionDenied("Вы не можете редактировать это сообщение")


class MessageDeleteView(LoginRequiredMixin, DeleteView):
    model = Message
    template_name = 'mailing/message_delete.html'
    success_url = reverse_lazy('mailing:home')

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        # Очищаем кеш после удаления сообщения
        cache.delete_pattern('*user_home_stats_*')
        return response

    def dispatch(self, request, *args, **kwargs):
        message = self.get_object()
        user = request.user

        if user_is_manager(user):
            return super().dispatch(request, *args, **kwargs)

        if Mailing.objects.filter(owner=user, message=message).exists():
            return super().dispatch(request, *args, **kwargs)

        raise PermissionDenied("Вы не можете удалить это сообщение")


# Рассылки - с использованием миксина
class MailingListView(LoginRequiredMixin, ListView):
    model = Mailing
    template_name = 'mailing/mailing_list.html'
    context_object_name = 'mailings'

    def get_queryset(self):
        user = self.request.user

        # Используем кеширование для списка рассылок
        cache_key = f"mailings_list_{user.id}"
        cached_mailings = cache.get(cache_key)

        if cached_mailings:
            return cached_mailings

        if user_is_manager(user):
            # Менеджеры видят все рассылки
            mailings = Mailing.objects.select_related('message', 'owner').all()
        else:
            # Пользователи видят только свои
            mailings = Mailing.objects.select_related('message', 'owner').filter(owner=user)

        # Кешируем на 1 минуту
        cache.set(cache_key, mailings, 60)
        return mailings


class MailingDetail(OwnerOrManagerRequiredMixin, DetailView):
    model = Mailing
    template_name = 'mailing/mailing.html'
    context_object_name = 'mailing'

    @method_decorator(cache_page(60 * 2))  # Кешируем страницу на 2 минуты
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()
        return obj


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = 'mailing/mailing_form.html'
    success_url = reverse_lazy('mailing:mailing_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        # Очищаем кеши после создания рассылки
        user = self.request.user
        cache.delete(f"mailings_list_{user.id}")
        cache.delete(f"user_home_stats_{user.id}")
        return response


class MailingUpdateView(OwnerOrManagerRequiredMixin, UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = 'mailing/mailing_edit.html'
    success_url = reverse_lazy('mailing:mailing_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Очищаем кеши после обновления рассылки
        mailing = self.object
        cache.delete(f"mailings_list_{mailing.owner.id}")
        cache.delete(f"user_home_stats_{mailing.owner.id}")
        return response


class MailingDeleteView(OwnerOrManagerRequiredMixin, DeleteView):
    model = Mailing
    template_name = 'mailing/mailing_delete.html'
    success_url = reverse_lazy('mailing:mailing_list')

    def delete(self, request, *args, **kwargs):
        mailing = self.get_object()
        owner_id = mailing.owner.id
        response = super().delete(request, *args, **kwargs)
        # Очищаем кеши после удаления рассылки
        cache.delete(f"mailings_list_{owner_id}")
        cache.delete(f"user_home_stats_{owner_id}")
        return response


class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Миксин для проверки что пользователь менеджер"""

    def test_func(self):
        user = self.request.user
        # Проверяем, состоит ли пользователь в группе Менеджеры
        return user.groups.filter(name='Менеджеры').exists()

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("Только менеджеры могут выполнять это действие")
        return super().handle_no_permission()


# Список пользователей для менеджеров
class UserListView(ManagerRequiredMixin, ListView):
    model = CustomUser
    template_name = 'mailing/user_list.html'
    context_object_name = 'users'

    @method_decorator(cache_page(60 * 10))  # Кешируем страницу на 10 минут
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        # Используем кеширование для списка пользователей
        cache_key = "users_list_managers"
        cached_users = cache.get(cache_key)

        if cached_users:
            return cached_users

        # Показываем всех пользователей кроме суперпользователей
        users = CustomUser.objects.filter(is_superuser=False) \
            .annotate(
            mailing_count=Count('mailing', distinct=True),
            active_mailing_count=Count('mailing', filter=Q(mailing__status='Запущена'), distinct=True)
        ) \
            .order_by('email')

        # Кешируем на 5 минут
        cache.set(cache_key, users, 300)
        return users

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Кешируем общую статистику
        cache_key = "users_stats"
        cached_stats = cache.get(cache_key)

        if cached_stats:
            context.update(cached_stats)
        else:
            stats = {
                'total_users': CustomUser.objects.filter(is_superuser=False).count(),
                'active_users': CustomUser.objects.filter(is_superuser=False, is_active=True).count(),
                'blocked_users': CustomUser.objects.filter(is_superuser=False, is_active=False).count(),
            }
            cache.set(cache_key, stats, 120)  # 2 минуты
            context.update(stats)

        return context


# Блокировка/разблокировка пользователя
class UserToggleBlockView(ManagerRequiredMixin, UpdateView):
    model = CustomUser
    fields = []  # Мы не используем форму
    template_name = 'mailing/user_confirm_block.html'

    def get_success_url(self):
        return reverse_lazy('mailing:user_list')

    def form_valid(self, form):
        user = self.object

        if user.is_active:
            # Блокируем пользователя
            user.is_active = False
            messages.warning(
                self.request,
                f'Пользователь {user.email} заблокирован'
            )
            # Дополнительно: блокируем все активные рассылки пользователя
            active_mailings = Mailing.objects.filter(owner=user, status='Запущена')
            for mailing in active_mailings:
                mailing.status = 'Заблокирована'
                mailing.save()
        else:
            # Разблокируем пользователя
            user.is_active = True
            messages.success(
                self.request,
                f'Пользователь {user.email} разблокирован'
            )

        user.save()

        # Очищаем кеши после изменения статуса пользователя
        cache.delete("users_list_managers")
        cache.delete("users_stats")
        cache.delete_pattern('*user_home_stats_*')
        cache.delete_pattern('*mailings_list_*')

        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'block' if self.object.is_active else 'unblock'
        return context


# Отключение рассылок
class MailingToggleView(ManagerRequiredMixin, UpdateView):
    model = Mailing
    fields = []  # Мы не используем форму
    template_name = 'mailing/mailing_confirm_toggle.html'

    def get_success_url(self):
        return reverse_lazy('mailing:mailing')

    def form_valid(self, form):
        mailing = self.object

        if mailing.status == 'Запущена':
            # Отключаем рассылку
            mailing.status = 'Отключена менеджером'
            messages.warning(
                self.request,
                f'Рассылка #{mailing.id} отключена'
            )
        elif mailing.status == 'Отключена менеджером':
            # Включаем рассылку обратно
            mailing.update_status()  # Используем существующий метод для определения статуса
            messages.success(
                self.request,
                f'Рассылка #{mailing.id} включена'
            )

        mailing.save()

        # Очищаем кеши после изменения статуса рассылки
        owner_id = mailing.owner.id if mailing.owner else None
        if owner_id:
            cache.delete(f"mailings_list_{owner_id}")
            cache.delete(f"user_home_stats_{owner_id}")
        cache.delete("users_stats")

        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'disable' if self.object.status == 'Запущена' else 'enable'
        return context


# Быстрое отключение рассылки без подтверждения
def mailing_disable_quick(request, pk):
    """Быстрое отключение рассылки (для использования из списка)"""
    if not request.user.groups.filter(name='Менеджеры').exists():
        raise PermissionDenied("Только менеджеры могут выполнять это действие")

    mailing = get_object_or_404(Mailing, pk=pk)

    if mailing.status == 'Запущена':
        mailing.status = 'Отключена менеджером'
        mailing.save()
        messages.warning(request, f'Рассылка #{mailing.id} отключена')

        # Очищаем кеши после отключения рассылки
        owner_id = mailing.owner.id if mailing.owner else None
        if owner_id:
            cache.delete(f"mailings_list_{owner_id}")
            cache.delete(f"user_home_stats_{owner_id}")
        cache.delete("users_stats")

    return redirect('mailing:mailing')
