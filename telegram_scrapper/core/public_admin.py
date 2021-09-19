from django.utils.safestring import mark_safe
from public_admin.admin import PublicModelAdmin
from public_admin.sites import PublicAdminSite, PublicApp

from .models import Message, TelegramUser, Group


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
    fields = ['user_id', 'username', 'full_name']
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


class GroupModelAdmin(PublicModelAdmin):
    search_fields = ['id']
    list_display = ('id', 'total_messages', 'active')
    fields = ['id', 'total_messages', 'active']

    def total_messages(self, obj):
        return Message.objects.filter(group=obj.id).count()

    total_messages.short_description = 'Mensagens armazenadas'


class MessageModelAdmin(PublicModelAdmin):
    PROCESSING_MESSAGE = "Processando, volte mais tarde."

    search_fields = ['message']
    list_display = (
        'id',
        'group',
        'sender_link',
        'message',
        'has_audio',
        'has_document',
        'has_image',
        'has_video',
        'sent_at',
    )
    fields = [
        'id',
        'message_id',
        'group',
        'sender_link',
        'sent_at',
        'forwarded',
        'message',
        'photo_tag',
        'audio_tag',
    ]
    ordering = ['-sent_at']
    list_filter = ['group']

    @mark_safe
    def sender_link(self, obj):
        return (
            f"<a href=\"/dashboard/core/telegramuser/{obj.sender}\" >{obj.sender}</a>"
        )

    @mark_safe
    def photo_tag(self, obj):
        return (
            (
                f"<img src=\"{obj.photo_url}\" />"
                if obj.photo_url
                else self.PROCESSING_MESSAGE
            )
            if self.has_image(obj)
            else "-"
        )

    @mark_safe
    def audio_tag(self, obj):
        return (
            (
                "<audio controls preload=\"metadata\" style=\" width:300px;\"><source"
                f" src=\"{obj.audio_url}\" type=\"audio/mpeg\">Navegador não suporta,"
                f" acesse {obj.audio_url}.</audio>"
                if obj.audio_url
                else self.PROCESSING_MESSAGE
            )
            if self.has_audio(obj)
            else "-"
        )

    def has_audio(self, obj):
        return bool(obj.audio)

    def has_document(self, obj):
        return bool(obj.document)

    def has_image(self, obj):
        return bool(obj.photo)

    def has_video(self, obj):
        return bool(obj.video)

    photo_tag.short_description = 'Imagem'
    photo_tag.allow_tags = True

    audio_tag.short_description = 'Audio'
    audio_tag.allow_tags = True

    sender_link.short_description = "Remetente"
    sender_link.allow_tags = True

    has_audio.boolean = True
    has_audio.short_description = "audio"

    has_document.boolean = True
    has_document.short_description = "documento"

    has_image.boolean = True
    has_image.short_description = "imagem"

    has_video.boolean = True
    has_video.short_description = "video"


public_app = PublicApp("core", models=["Message", "TelegramUser", "Group"])
public_admin = PublicAdminSite("dashboard", public_app)
public_admin.register(Message, MessageModelAdmin)
public_admin.register(TelegramUser, TelegramUserModelAdmin)
public_admin.register(Group, GroupModelAdmin)
