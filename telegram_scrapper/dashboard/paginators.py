import json

from django.core.paginator import Paginator
from django.utils.functional import cached_property

from telegram_scrapper.core.models import Report

class MessagesPaginator(Paginator):

    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True, has_filter=False):
        super(MessagesPaginator, self).__init__(object_list, per_page, orphans, allow_empty_first_page)
        self._object_list = object_list
        self._has_filter = has_filter
    
    @cached_property
    def count(self):
        if self._has_filter:
            return self._object_list.count()
        else:
            messages_data = Report.objects.get(id='general_messages').report_data
            total_messages = json.loads(messages_data)['count']
            return total_messages