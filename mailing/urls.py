from django.urls import path
from mailing.views import (
    Home,
    ReceiverDetail, ReceiverCreateView, ReceiverUpdateView, ReceiverDeleteView,
    MessageDetail, MessageCreateView, MessageUpdateView, MessageDeleteView,
    MailingDetail, MailingCreateView, MailingUpdateView, MailingDeleteView,
    UserListView, UserToggleBlockView, MailingToggleView, mailing_disable_quick
)

app_name = 'mailing'

urlpatterns = [
    # Главная
    path('home/', Home.as_view(), name='home'),

    # Получатели
    path('receiver/<int:pk>/', ReceiverDetail.as_view(), name='receiver'),
    path('receiver/add/', ReceiverCreateView.as_view(), name='receiver-create'),
    path('receiver/<int:pk>/edit/', ReceiverUpdateView.as_view(), name='receiver-update'),
    path('receiver/<int:pk>/delete/', ReceiverDeleteView.as_view(), name='receiver-delete'),

    # Сообщения
    path('message/<int:pk>/', MessageDetail.as_view(), name='message'),
    path('message/add/', MessageCreateView.as_view(), name='message-create'),
    path('message/<int:pk>/edit/', MessageUpdateView.as_view(), name='message-update'),
    path('message/<int:pk>/delete/', MessageDeleteView.as_view(), name='message-delete'),

    # Рассылки
    path('mailing/<int:pk>/', MailingDetail.as_view(), name='mailing'),
    path('mailing/add/', MailingCreateView.as_view(), name='mailing-create'),
    path('mailing/<int:pk>/edit/', MailingUpdateView.as_view(), name='mailing-update'),
    path('mailing/<int:pk>/delete/', MailingDeleteView.as_view(), name='mailing-delete'),

    # Управление для менеджеров
    path('manager/users/', UserListView.as_view(), name='user_list'),
    path('manager/user/<int:pk>/toggle-block/', UserToggleBlockView.as_view(), name='user_toggle_block'),
    path('manager/mailing/<int:pk>/toggle/', MailingToggleView.as_view(), name='mailing_toggle'),
    path('manager/mailing/<int:pk>/disable-quick/', mailing_disable_quick, name='mailing_disable_quick'),
]