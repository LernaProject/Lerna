import contextlib

from ajax_select       import register, LookupChannel
from django.db.models  import Q
from django.utils.html import escape

from .models import User


@register('users')
class UserLookup(LookupChannel):
    model = User

    def get_query(self, q, request):
        query = Q(login__icontains=q) | Q(username__icontains=q) | Q(email__icontains=q)
        with contextlib.suppress(ValueError):
            query |= Q(id=int(q))
        return (
            self.model
            .objects
            .filter(query)
            .order_by('username')
            .only('id', 'login', 'username')
        )[:50]

    def format_match(self, user):
        return escape(user)
