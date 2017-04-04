from django.conf import settings

import pygments.formatters
import pygments.lexers.special


def format_time(minutes):
    return '%d:%02d' % divmod(minutes, 60) if minutes >= 0 else '-%d:%02d' % divmod(-minutes, 60)


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
