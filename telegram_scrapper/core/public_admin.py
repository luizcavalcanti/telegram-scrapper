from public_admin.admin import PublicModelAdmin
from public_admin.sites import PublicAdminSite, PublicApp

from .models import Message


class MessageModelAdmin(PublicModelAdmin):
    search_fields = ['message']
    list_display = (
        'message_id',
        'group',
        'sender',
        'message',
        'has_audio',
        'has_image',
        'has_video',
        'sent_at',
    )
    ordering = ['-sent_at']
    list_filter = ['group']

    def has_audio(self, obj):
        return bool(obj.audio)

    def has_image(self, obj):
        return bool(obj.photo)

    def has_video(self, obj):
        return bool(obj.video)

    has_audio.boolean = True
    has_image.boolean = True
    has_video.boolean = True

    has_audio.short_description = "audio"
    has_image.short_description = "imagem"
    has_video.short_description = "video"


public_app = PublicApp("core", models=["Message"])
public_admin = PublicAdminSite("dashboard", public_app)
public_admin.register(Message, MessageModelAdmin)
