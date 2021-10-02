from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F
from django.utils.safestring import mark_safe
from public_admin.admin import PublicModelAdmin
from public_admin.sites import PublicAdminSite, PublicApp

from .models import Message, TelegramUser, Group
from .render_utils import (
    render_message,
    render_image,
    render_video_player,
    render_audio_player,
)

PROCESSING_MESSAGE = "Processando, volte mais tarde."


class TelegramUserModelAdmin(PublicModelAdmin):
    LAST_MESSAGES_LIMIT = 20
    search_fields = ['user_id', 'username', 'first_name', 'last_name']
    list_display = (
        'user_id',
        'username',
        'full_name',
        'is_verified',
        'is_fake',
        'is_deleted',
    )
    fields = [
        'user_id',
        'username',
        'full_name',
        'total_messages',
        'groups',
        'last_messages',
    ]
    exclude = ['phone']
    ordering = ['user_id', 'username']
    list_filter = ['verified', 'deleted', 'fake']

    def full_name(self, obj):
        return (
            f"{obj.first_name if obj.first_name else ''}"
            f" {obj.last_name if obj.last_name else ''}"
        )

    def total_messages(self, obj):
        return Message.objects.filter(sender=obj.user_id).count()

    def groups(self, obj):
        return ', '.join(
            map(
                lambda m: m['group'],
                Message.objects.filter(sender=obj.user_id)
                .values('group')
                .distinct('group')
                .order_by('group'),
            )
        )

    @mark_safe
    def last_messages(self, obj):
        return '<br>'.join(
            map(
                lambda m: render_message(m),
                Message.objects.filter(sender=obj.user_id).order_by('-sent_at')[
                    : self.LAST_MESSAGES_LIMIT
                ],
            )
        )

    def is_verified(self, obj):
        return bool(obj.verified)

    def is_fake(self, obj):
        return bool(obj.fake)

    def is_deleted(self, obj):
        return bool(obj.deleted)

    is_verified.boolean = True
    is_fake.boolean = True
    is_deleted.boolean = True

    is_verified.short_description = "Verificado"
    is_fake.short_description = "Fake"
    is_deleted.short_description = "Excluído"
    full_name.short_description = "Nome"
    total_messages.short_description = "Mensagens postadas"
    groups.short_description = "Grupos"

    last_messages.short_description = "Últimas mensagens"
    last_messages.allow_tags = True


class GroupModelAdmin(PublicModelAdmin):
    LAST_MESSAGES_LIMIT = 30
    search_fields = ['id']
    list_display = ('id', 'total_messages', 'active')
    fields = ['id', 'total_messages', 'active', 'last_messages']

    def total_messages(self, obj):
        return Message.objects.filter(group=obj.id).count()

    @mark_safe
    def last_messages(self, obj):
        return '<br>'.join(
            map(
                lambda m: render_message(m),
                Message.objects.filter(group=obj.id).order_by('-sent_at')[
                    : self.LAST_MESSAGES_LIMIT
                ],
            )
        )

    total_messages.short_description = 'Mensagens armazenadas'
    last_messages.short_description = "Últimas mensagens"
    last_messages.allow_tags = True


class MessageModelAdmin(PublicModelAdmin):

    search_fields = ['message']
    list_display = (
        'id',
        'group_link',
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
        'group_link',
        'sender_link',
        'sent_at',
        'forwarded',
        'message',
        'photo_tag',
        'audio_tag',
        'video_tag',
    ]
    ordering = ['-sent_at']
    list_filter = ['group']

    def get_search_results(self, request, queryset, search_term):
        if not search_term:
            return super(MessageModelAdmin, self).get_search_results(
                request, queryset, search_term
            )

        query = SearchQuery(search_term, config="portuguese")
        queryset = (
            Message.objects.annotate(rank=SearchRank(F("search_vector"), query))
            .filter(search_vector=query)
            .order_by("-rank")
        )
        return queryset, False

    @mark_safe
    def sender_link(self, obj):
        return (
            f"<a href=\"/dashboard/core/telegramuser/{obj.sender}\" >{obj.sender}</a>"
            if obj.sender != 'channel'
            else 'canal'
        )

    @mark_safe
    def group_link(self, obj):
        return f"<a href=\"/dashboard/core/group/{obj.group}\" >{obj.group}</a>"

    @mark_safe
    def photo_tag(self, obj):
        return (
            (render_image(obj.photo_url) if obj.photo_url else PROCESSING_MESSAGE)
            if self.has_image(obj)
            else "-"
        )

    @mark_safe
    def audio_tag(self, obj):
        return (
            (
                render_audio_player(obj.audio_url)
                if obj.audio_url
                else PROCESSING_MESSAGE
            )
            if self.has_audio(obj)
            else "-"
        )

    @mark_safe
    def video_tag(self, obj):
        return (
            (
                render_video_player(obj.video_url)
                if obj.video_url
                else PROCESSING_MESSAGE
            )
            if self.has_video(obj)
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

    video_tag.short_description = 'Video'
    video_tag.allow_tags = True

    sender_link.short_description = "Remetente"
    sender_link.allow_tags = True

    group_link.short_description = "Grupo"
    group_link.allow_tags = True

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

public_admin.site_header = "Telegram Scrapper"
public_admin.site_title = "Telegram Scrapper"
public_admin.index_title = "Dados"
