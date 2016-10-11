from ajax_select       import register, LookupChannel
from django.db.models  import Q
from django.utils.html import escape

from .models import User


@register('users')
class UserLookup(LookupChannel):
    model = User

    def get_query(self, q, request):
        return (
            self.model
            .objects
            .filter(Q(login__icontains=q) | Q(username__icontains=q) | Q(email__icontains=q))
            .order_by('username')
            .only('id', 'login', 'username')
        )[:50]

    def format_match(self, user):
        return escape(user)

    def format_item_display(self, user):
        return escape('%s (%s)' % (user.username, user.login))
