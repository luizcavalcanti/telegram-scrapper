from django.utils.safestring import mark_safe
from public_admin.admin import PublicModelAdmin
from public_admin.sites import PublicAdminSite, PublicApp

from .models import Message, TelegramUser


class TelegramUserModelAdmin(PublicModelAdmin):
    search_fields = ['user_id', 'username', 'first_name', 'last_name']
    list_display = (
        'user_id',
        'username',
        'full_name',
        'is_verified',
        'is_fake',
        'is_deleted',
    )
    exclude = ['phone']
    ordering = ['user_id', 'username']
    list_filter = ['verified', 'deleted', 'fake']

    def full_name(self, obj):
        return (
            f"{obj.first_name if obj.first_name else ''}"
            f" {obj.last_name if obj.last_name else ''}"
        )

    def is_verified(self, obj):
        return bool(obj.verified)

    def is_fake(self, obj):
        return bool(obj.fake)

    def is_deleted(self, obj):
        return bool(obj.deleted)

    is_verified.boolean = True
    is_verified.short_description = "Verificado"

    is_fake.boolean = True
    is_fake.short_description = "Fake"

    is_deleted.boolean = True
    is_deleted.short_description = "Excluído"


class MessageModelAdmin(PublicModelAdmin):
    search_fields = ['message']
    list_display = (
        'id',
        'group',
        'link_sender',
        'message',
        'has_audio',
        'has_document',
        'has_image',
        'has_video',
        'sent_at',
    )
    ordering = ['-sent_at']
    list_filter = ['group']

    @mark_safe
    def link_sender(self, obj):
        return (
            f"<a href=\"/dashboard/core/telegramuser/{obj.sender}\" />{obj.sender}</a>"
        )

    def has_audio(self, obj):
        return bool(obj.audio)

    def has_document(self, obj):
        return bool(obj.document)

    def has_image(self, obj):
        return bool(obj.photo)

    def has_video(self, obj):
        return bool(obj.video)

    link_sender.short_description = "Remetente"
    link_sender.allow_tags = True

    has_audio.boolean = True
    has_audio.short_description = "audio"

    has_document.boolean = True
    has_document.short_description = "documento"

    has_image.boolean = True
    has_image.short_description = "imagem"

    has_video.boolean = True
    has_video.short_description = "video"


public_app = PublicApp("core", models=["Message", "TelegramUser"])
public_admin = PublicAdminSite("dashboard", public_app)
public_admin.register(Message, MessageModelAdmin)
public_admin.register(TelegramUser, TelegramUserModelAdmin)
