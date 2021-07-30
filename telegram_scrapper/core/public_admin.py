from public_admin.admin import PublicModelAdmin
from public_admin.sites import PublicAdminSite, PublicApp

from .models import Message


class MessageModelAdmin(PublicModelAdmin):
	search_fields = ['message']
	list_display = ('message_id', 'group', 'sender', 'message', 'sent_at')
	ordering = ['-sent_at']
	list_filter = ['group']



public_app = PublicApp("core", models=["Message"])
public_admin = PublicAdminSite("dashboard", public_app)
public_admin.register(Message, MessageModelAdmin)