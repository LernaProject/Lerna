from django import template

register = template.Library()


@register.filter(name='to_ordering_letter')
def to_ordering_letter(number):
    return chr(ord('A') + (number - 1))
