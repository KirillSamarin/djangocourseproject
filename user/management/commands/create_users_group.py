from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from mailing.models import Mailing, Message, ReceiverMailing
from user.models import CustomUser


class Command(BaseCommand):
    help = 'Создает группы Пользователи и Менеджеры с расширенными правами'

    def handle(self, *args, **options):
        # Создаем группу Пользователи
        user_group, created = Group.objects.get_or_create(name='Пользователи')
        if created:
            self.stdout.write(self.style.SUCCESS("Создана группа: Пользователи"))
        else:
            self.stdout.write(self.style.WARNING("Группа Пользователи уже существует"))

        # Создаем группу Менеджеры
        manager_group, created = Group.objects.get_or_create(name='Менеджеры')
        if created:
            self.stdout.write(self.style.SUCCESS("Создана группа: Менеджеры"))
        else:
            self.stdout.write(self.style.WARNING("Группа Менеджеры уже существует"))

        # Получаем ContentType для моделей
        mailing_ct = ContentType.objects.get_for_model(Mailing)
        message_ct = ContentType.objects.get_for_model(Message)
        receiver_ct = ContentType.objects.get_for_model(ReceiverMailing)
        user_ct = ContentType.objects.get_for_model(CustomUser)

        # РАЗРЕШЕНИЯ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ:
        # 1. Создание, просмотр, редактирование и удаление своих клиентов
        user_receiver_permissions = [
            (receiver_ct, 'add_receivermailing'),  # Создание клиентов
            (receiver_ct, 'view_receivermailing'),  # Просмотр клиентов
            (receiver_ct, 'change_receivermailing'),  # Редактирование клиентов
            (receiver_ct, 'delete_receivermailing'),  # Удаление клиентов
        ]

        # 2. Создание, просмотр, редактирование и удаление своих сообщений
        user_message_permissions = [
            (message_ct, 'add_message'),  # Создание сообщений
            (message_ct, 'view_message'),  # Просмотр сообщений
            (message_ct, 'change_message'),  # Редактирование сообщений
            (message_ct, 'delete_message'),  # Удаление сообщений
        ]

        # 3. Создание, просмотр, редактирование и удаление своих рассылок
        user_mailing_permissions = [
            (mailing_ct, 'add_mailing'),  # Создание рассылок
            (mailing_ct, 'view_mailing'),  # Просмотр рассылок
            (mailing_ct, 'change_mailing'),  # Редактирование рассылок
            (mailing_ct, 'delete_mailing'),  # Удаление рассылок
        ]

        # Объединяем все разрешения для пользователей
        all_user_permissions = (user_receiver_permissions + user_message_permissions + user_mailing_permissions)

        self.stdout.write(self.style.SUCCESS("\n=== ДОБАВЛЕНИЕ РАЗРЕШЕНИЙ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ==="))
        for content_type, codename in all_user_permissions:
            try:
                permission = Permission.objects.get(
                    content_type=content_type,
                    codename=codename
                )
                user_group.permissions.add(permission)
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Пользователи: добавлено '{codename}'")
                )
            except Permission.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"✗ Разрешение '{codename}' не найдено")
                )

        # РАЗРЕШЕНИЯ ДЛЯ МЕНЕДЖЕРОВ:
        # 1. Просмотр всех клиентов, сообщений и рассылок
        manager_view_permissions = [
            (receiver_ct, 'view_receivermailing'),  # Просмотр всех клиентов
            (message_ct, 'view_message'),  # Просмотр всех сообщений
            (mailing_ct, 'view_mailing'),  # Просмотр всех рассылок
        ]

        # 2. Просмотр списка пользователей сервиса и блокировка
        manager_user_permissions = [
            (user_ct, 'view_customuser'),  # Просмотр списка пользователей
            (user_ct, 'change_customuser'),  # Блокировка пользователей (через is_active)
        ]

        # 3. Отключение рассылок (через change_mailing)
        manager_mailing_control_permissions = [
            (mailing_ct, 'change_mailing'),  # Отключение рассылок
        ]

        # Объединяем все разрешения для менеджеров
        all_manager_permissions = (manager_view_permissions + manager_user_permissions + manager_mailing_control_permissions)

        self.stdout.write(self.style.SUCCESS("\n=== ДОБАВЛЕНИЕ РАЗРЕШЕНИЙ ДЛЯ МЕНЕДЖЕРОВ ==="))
        for content_type, codename in all_manager_permissions:
            try:
                permission = Permission.objects.get(
                    content_type=content_type,
                    codename=codename
                )
                manager_group.permissions.add(permission)
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Менеджеры: добавлено '{codename}'")
                )
            except Permission.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"✗ Разрешение '{codename}' не найдено")
                )

        # ИТОГИ
        self.stdout.write(self.style.SUCCESS("\n=== ИТОГИ ==="))
        self.stdout.write(self.style.SUCCESS(f"✓ Группа 'Пользователи': {user_group.permissions.count()} разрешений"))
        self.stdout.write(self.style.SUCCESS(f"✓ Группа 'Менеджеры': {manager_group.permissions.count()} разрешений"))
        self.stdout.write(self.style.SUCCESS("\nГруппы и разрешения созданы успешно!"))

        # Выводим подробную информацию о добавленных разрешениях
        self.stdout.write(self.style.SUCCESS("\n=== ПРАВА ПОЛЬЗОВАТЕЛЕЙ ==="))
        self.stdout.write("1. Создание, просмотр, редактирование и удаление своих клиентов")
        self.stdout.write("2. Создание, просмотр, редактирование и удаление своих сообщений")
        self.stdout.write("3. Создание, просмотр, редактирование и удаление своих рассылок")
        self.stdout.write("4. Просмотр статистики по своим рассылкам (через кастомный view)")

        self.stdout.write(self.style.SUCCESS("\n=== ПРАВА МЕНЕДЖЕРОВ ==="))
        self.stdout.write("1. Просмотр всех клиентов и рассылок")
        self.stdout.write("2. Просмотр списка пользователей сервиса")
        self.stdout.write("3. Блокировка пользователей сервиса")
        self.stdout.write("4. Отключение рассылок")
