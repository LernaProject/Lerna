import textwrap

from django.conf    import settings
from django.contrib import messages
from django.urls    import reverse
from django.utils   import html

from   messages_extends        import constants as msg_lvl
from   messages_extends.models import Message
import pygments.formatters
import pygments.lexers.special

from users.util import notify_admins


def format_time(minutes):
    if minutes >= 0:
        return '%d:%02d' % divmod(minutes, 60)
    else:
        return '\u2012%d:%02d' % divmod(-minutes, 60)


def _find_lexer(name, **kwargs):
    try:
        return pygments.lexers.get_lexer_by_name(name, **kwargs)
    except pygments.util.ClassNotFound:
        # TODO: Log that.
        return pygments.lexers.special.TextLexer(**kwargs)


def highlight_source(source, highlighter):
    cnf = settings.PYGMENTS
    lexer = _find_lexer(highlighter, **cnf.get('LEXER', { }))
    formatter = pygments.formatters.HtmlFormatter(**cnf.get('FORMATTER', { }))
    html = pygments.highlight(source, lexer, formatter)
    return html, formatter.get_style_defs(cnf.get('STYLE_SELECTORS', ''))


def notify_admins_about_clarification(request, clarification):
    notify_admins(
        request,
        msg_lvl.WARNING_PERSISTENT,
        '<a href="{}" data-clarification="{}">Задан новый вопрос</a>: "{}"'.format(
            reverse('admin:core_clarification_change', args=[clarification.id]),
            clarification.id,
            html.escape(clarification),
        ),
        safe=True,
    )


def notify_user_about_clarification(request, clarification):
    messages.add_message(
        request,
        msg_lvl.INFO_PERSISTENT,
        'На Ваш вопрос был <a href="{}" data-clarification="{}">дан ответ</a>: "{}"'.format(
            clarification.get_absolute_url(),
            clarification.id,
            html.escape(
                textwrap.shorten(html.strip_tags(clarification.answer_html), 70, placeholder='...')
            ),
        ),
        extra_tags='safe',
        user=clarification.user,
    )


def clear_clarification_messages(clarification):
    Message.objects.filter(message__contains='data-clarification="%d"' % clarification.id).delete()
