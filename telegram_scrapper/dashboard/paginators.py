import json

from django.core.paginator import Paginator
from django.utils.functional import cached_property

from telegram_scrapper.core.models import Report

class MessagesPaginator(Paginator):
    
    @cached_property
    def count(self):
        messages_data = Report.objects.get(id='general_messages').report_data
        total_messages = json.loads(messages_data)['count']
        return total_messages