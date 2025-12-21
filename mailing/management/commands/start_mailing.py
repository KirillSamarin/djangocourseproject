from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from mailing.models import Mailing, MailingAttempt
import smtplib


class Command(BaseCommand):
    help = 'Запускает конкретную рассылку по ID'

    def add_arguments(self, parser):
        parser.add_argument(
            'mailing_id',
            type=int,
            help='ID рассылки для запуска'
        )

    def handle(self, *args, **options):
        mailing_id = options['mailing_id']

        try:
            # Получаем рассылку
            mailing = Mailing.objects.get(id=mailing_id)
            self.stdout.write(f"Найдена рассылка #{mailing.id} - Статус: {mailing.status}")
            self.stdout.write(f"Сообщение: '{mailing.message.topic}'")

            # Проверка времени
            now = timezone.now()
            self.stdout.write(f"Текущее время: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            self.stdout.write(f"Время начала: {mailing.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.stdout.write(f"Время окончания: {mailing.end_time.strftime('%Y-%m-%d %H:%M:%S')}")

            if mailing.start_time <= now <= mailing.end_time:
                self.stdout.write(self.style.SUCCESS("✓ Время для рассылки подходящее"))
            else:
                self.stdout.write(self.style.ERROR("✗ Неподходящее время для рассылки!"))
                return

            # Получаем всех связанных получателей
            receivers = mailing.receivers.all()
            self.stdout.write(f"✓ Найдено получателей: {receivers.count()}")

            if not receivers.exists():
                self.stdout.write(self.style.WARNING("✗ Нет получателей для рассылки"))
                return

            # Отображаем получателей
            self.stdout.write("Список получателей:")
            for receiver in receivers:
                self.stdout.write(f"  - {receiver.full_name} <{receiver.email}>")

            # Подтверждение
            confirm = input("\nЗапустить рассылку? (y/n): ")
            if confirm.lower() != 'y':
                self.stdout.write("Отменено пользователем")
                return

            # Запускаем рассылку
            self.process_mailing(mailing, receivers)

        except Mailing.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Рассылка с ID {mailing_id} не найдена"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка: {str(e)}"))

    def process_mailing(self, mailing, receivers):
        """Обрабатывает рассылку для всех получателей"""
        success_count = 0
        fail_count = 0
        messages_count = 0

        # Обновляем статус рассылки
        mailing.status = 'Запущена'
        mailing.save()

        message = mailing.message
        self.stdout.write(f"\nНачинаю отправку сообщения: '{message.topic}'")
        self.stdout.write("-" * 50)

        for receiver in receivers:
            # Отправляем письмо каждому получателю
            result = self.send_email_to_receiver(message, receiver)

            if result['success']:
                success_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f"✓ {receiver.email}: отправлено успешно"
                ))
                # Создаем успешную попытку для каждого получателя
                MailingAttempt.objects.create(
                    mailing=mailing,
                    status='success',
                    server_response=result.get('response', 'Успешно')
                )
            else:
                fail_count += 1
                self.stdout.write(self.style.ERROR(
                    f"✗ {receiver.email}: ошибка"
                ))
                # Создаем неуспешную попытку для каждого получателя
                MailingAttempt.objects.create(
                    mailing=mailing,
                    status='failed',
                    server_response=result.get('response', 'Неизвестная ошибка')
                )

        messages_count = success_count + fail_count

        # Обновляем статус рассылки после отправки
        self.stdout.write("-" * 50)

        # Получаем владельца рассылки
        owner = mailing.owner

        # Обновляем счетчики пользователя
        if owner:
            owner.successful_mailing_count = (owner.successful_mailing_count or 0) + success_count
            owner.unsuccessful_mailing_count = (owner.unsuccessful_mailing_count or 0) + fail_count
            owner.messages_count = (owner.messages_count or 0) + messages_count
            owner.save()

        if success_count > 0 or fail_count > 0:
            mailing.status = 'Завершена'
            mailing.save()

            self.stdout.write(self.style.SUCCESS(
                f"\n✓ РАССЫЛКА ЗАВЕРШЕНА!\n"
                f"Успешно отправлено: {success_count}\n"
                f"Ошибок: {fail_count}\n"
                f"Общее количество сообщений: {messages_count}"
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f"\n✗ НИ ОДНОГО ПИСЬМА НЕ ОТПРАВЛЕНО!"
            ))

    def send_email_to_receiver(self, message, receiver):
        """Отправляет email конкретному получателю и возвращает ответ сервера"""
        try:
            # Персонализируем сообщение
            personalized_body = f"Здравствуйте, {receiver.full_name}!\n\n"
            personalized_body += message.text

            if receiver.comm:
                personalized_body += f"\n\nПримечание: {receiver.comm}"

            personalized_body += f"\n\n--\nЭто сообщение отправлено автоматически"

            send_mail(
                subject=message.topic,
                message=personalized_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[receiver.email],
                fail_silently=False  # Не игнорировать ошибки
            )

            if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
                response = "Email отправлен в консоль (режим тестирования)"
            else:
                response = "Email успешно отправлен на почтовый сервер"

            return {
                'success': True,
                'response': response
            }

        except smtplib.SMTPException as e:
            return {
                'success': False,
                'response': f"SMTP ошибка: {str(e)}"
            }
        except ConnectionError as e:
            return {
                'success': False,
                'response': f"Ошибка подключения: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'response': f"Ошибка отправки: {str(e)}"
            }