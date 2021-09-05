from django.contrib import admin
from django.db.models import Count
from django.db.models.functions import Lower
from django.utils.safestring import mark_safe
from .models import Message, Group, TelegramUser


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    search_fields = ['message']
    list_display = ('message_id', 'group', 'link_sender', 'message', 'sent_at')
    ordering = ['-sent_at']
    list_filter = ['group']

    @mark_safe
    def link_sender(self, obj):
        return f"<a href=\"/admin/core/telegramuser/{obj.sender}\" />{obj.sender}</a>"

    link_sender.short_description = "Remetente"
    link_sender.allow_tags = True


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    search_fields = ['user_id', 'username', 'first_name', 'last_name', 'phone']
    list_display = ('user_id', 'username', 'full_name', 'phone', 'verified')
    ordering = ['user_id']
    list_filter = ['verified']

    def full_name(self, obj):
        return (
            f"{obj.first_name if obj.first_name else ''}"
            f" {obj.last_name if obj.last_name else ''}"
        )


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'active')
    list_editable = ['active']
