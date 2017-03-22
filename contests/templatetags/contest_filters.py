from django import template

register = template.Library()


@register.filter(name='to_ordering_letter')
def to_ordering_letter(number):
    # ord('A') - 1 == 64
    return chr(number + 64)
