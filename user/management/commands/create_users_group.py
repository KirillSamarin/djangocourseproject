from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


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

        # Добавляем базовые разрешения для менеджеров в рассылках
        mailing_permissions = [
            'view_mailing', 'view_receivermailing', 'view_message'
        ]

        for perm_codename in mailing_permissions:
            try:
                permission = Permission.objects.get(
                    codename=perm_codename,
                    content_type__app_label='mailing'
                )
                manager_group.permissions.add(permission)
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Добавлено разрешение '{perm_codename}' в группу 'Менеджеры'")
                )
            except Permission.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"✗ Разрешение '{perm_codename}' не найдено")
                )

        # Добавляем разрешения для управления пользователями
        user_permissions = [
            'view_customuser',  # Просмотр списка пользователей
            'change_customuser',  # Блокировка/разблокировка (через is_active)
        ]

        for perm_codename in user_permissions:
            try:
                permission = Permission.objects.get(
                    codename=perm_codename,
                    content_type__app_label='user',
                    content_type__model='customuser'
                )
                manager_group.permissions.add(permission)
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Добавлено разрешение пользователей '{perm_codename}' в группу 'Менеджеры'")
                )
            except Permission.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"✗ Разрешение пользователей '{perm_codename}' не найдено")
                )

        self.stdout.write(self.style.SUCCESS("Группы созданы успешно!"))