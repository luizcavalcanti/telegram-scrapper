from django.contrib import admin
from django.db.models import Count
from django.db.models.functions import Lower
from .models import Message, MessageSummary


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('message_id', 'group', 'message', 'sent_at')
    ordering = ['-sent_at']


@admin.register(MessageSummary)
class MessageSummaryAdmin(admin.ModelAdmin):
    change_list_template = 'admin/message_summary_change_list.html'
    date_hierarchy = 'sent_at'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)

        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response

        metrics = {'total': Count('id')}

        response.context_data['summary'] = list(
            qs.values('group').annotate(**metrics).order_by(Lower('group'))
        )

        return response
