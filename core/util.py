import pygments.formatters
import pygments.lexers.special


def _find_lexer(name, **kwargs):
    try:
        return pygments.lexers.get_lexer_by_name(name, **kwargs)
    except pygments.util.ClassNotFound:
        # TODO: Log that.
        return pygments.lexers.special.TextLexer(**kwargs)


def highlight_source(source, highlighter):
    lexer = _find_lexer(highlighter, tabsize=4)
    formatter = pygments.formatters.HtmlFormatter(linenos='table', style='tango')
    html = pygments.highlight(source, lexer, formatter)
    return html, formatter.get_style_defs('.highlight')
