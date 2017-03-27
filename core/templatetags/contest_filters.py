from django import template

register = template.Library()


@register.filter
def to_ordering_letter(number):
    try:
        # ord('A') - 1 == 64
        return chr(int(number) + 64)
    except ValueError:
        return ''
