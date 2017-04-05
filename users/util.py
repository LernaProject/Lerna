from django.contrib import messages

from users.models import User


def notify_admins(request, level, text, *, safe=False):
    for user in User.objects.filter(rights__gte=0x4):
        messages.add_message(request, level, text, user=user, extra_tags=('safe' if safe else None))
