import contextlib
import re

from ajax_select       import register, LookupChannel
from django.db.models  import Q
from django.utils.html import escape

from . import models


@register('achievements')
class AchievementLookup(LookupChannel):
    model = models.Achievement

    def get_query(self, q, request):
        query = Q(name__icontains=q)
        with contextlib.suppress(ValueError):
            query |= Q(id=int(q))
        return (
            self.model
            .objects
            .filter(query)
            .order_by('-id')
            .only('id', 'name')
        )[:50]

    def format_match(self, achievement):
        return escape(achievement)

    format_item_display = format_match
