from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F
from django.utils.safestring import mark_safe
from public_admin.admin import PublicModelAdmin
from public_admin.sites import PublicAdminSite, PublicApp

from .models import Message, TelegramUser, Group


# TODO: refatorar
def get_message_as_html(msg):
    header = (
        f"<a href='/dashboard/core/message/{msg.id}'>&gt;&gt;</a> [{msg.group}] "
        f" {msg.sent_at.strftime('%d/%m/%Y %H:%M:%S')}"
    )
    html_output = (
        f"<img style='max-height: 200px; margin: 3px' src='{msg.photo_url}'>"
        if msg.photo_url
        else ''
    )
    html_output += f"<audio src='{msg.audio_url}'>" if msg.audio_url else ''
    html_output += ' ' + msg.message if msg.message else ''
    html_output += (
        '<span style="color: red;">(video ainda não é suportado)</span>'
        if msg.video
        else ''
    )
    html_output += (
        '<span style="color: red;">(documento ainda não é suportado)</span>'
        if msg.document
        else ''
    )

    if html_output == '':
        return f"{header} - {str(msg.video)}"

    return f"{header} - {html_output}"


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
                lambda m: get_message_as_html(m),
                Message.objects.filter(sender=obj.user_id).order_by('-sent_at')[:10],
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
    last_messages.short_description = "Últimas mensagens"
    groups.short_description = "Grupos"


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

public_admin.site_header = "Telegram Scrapper"
public_admin.site_title = "Telegram Scrapper"
public_admin.index_title = "Dados"
