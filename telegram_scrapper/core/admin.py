from django.contrib import admin
from django.db.models import Count
from django.db.models.functions import Lower
from .models import Message, Group


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    search_fields = ['message']
    list_display = ('message_id', 'group', 'sender', 'message', 'sent_at')
    ordering = ['-sent_at']
    list_filter = ['group']


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'active')
