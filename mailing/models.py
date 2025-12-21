from django.db import models
from django.utils import timezone
from user.models import CustomUser


class ReceiverMailing(models.Model):

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150)
    comm = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'{self.email}, {self.full_name}'

    class Meta:
        verbose_name = 'получатель рассылки'
        verbose_name_plural = 'получатели рассылки'

class Message(models.Model):

    topic = models.CharField()
    text = models.TextField()

    def __str__(self):
        return f'{self.topic}'

    class Meta:
        verbose_name = 'сообщение'
        verbose_name_plural = 'сообщения'

class Mailing(models.Model):

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(default='Создана')
    owner = models.ForeignKey(CustomUser, verbose_name='Владелец', on_delete=models.CASCADE, null=True)
    message = models.ForeignKey(Message, verbose_name='Сообщение', on_delete=models.CASCADE, related_name='receivers')
    receivers = models.ManyToManyField(ReceiverMailing)

    def __str__(self):
        return f'{self.status}'

    def update_status(self):
        if timezone.now() < self.start_time:
            self.status = 'Создана'

        elif self.start_time <= timezone.now() <= self.end_time:
            self.status = 'Запущена'

        elif timezone.now() > self.end_time:
            self.status = 'Завершена'

    class Meta:
        verbose_name = 'рассылка'
        verbose_name_plural = 'рассылки'


class MailingAttempt(models.Model):
    STATUS_CHOICES = [
        ('success', 'Успешно'),
        ('failed', 'Не успешно'),
    ]

    attempt_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата и время попытки'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        verbose_name='Статус'
    )
    server_response = models.TextField(
        verbose_name='Ответ почтового сервера',
        blank=True
    )
    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name='Рассылка'
    )

    def __str__(self):
        return f"Попытка #{self.mailing} - {self.status} - {self.attempt_time}"

    class Meta:
        verbose_name = 'попытка рассылки'
        verbose_name_plural = 'попытки рассылки'
        ordering = ['-attempt_time']