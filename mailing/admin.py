from django.contrib import admin
from .models import ReceiverMailing

@admin.register(ReceiverMailing)
class ReceiverMailingAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name")
    search_fields = ("email", "full_name")
