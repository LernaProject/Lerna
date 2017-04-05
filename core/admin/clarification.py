from ajax_select              import make_ajax_form
from django                   import forms
from django.contrib           import admin
from django.utils.translation import ugettext as _

from jquery_model_admin import JQueryModelAdmin

from core      import models
from core.util import (
    notify_admins_about_clarification, notify_user_about_clarification, clear_clarification_messages
)


class ClarificationAnswerFilter(admin.SimpleListFilter):
    title = _('has answer')

    parameter_name = 'has_answer'

    def lookups(self, request, model_admin):
        return (
            ('1', _('Yes')),
            ('0', _('No')),
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        elif self.value() == '1':
            return queryset.exclude(answer='')
        else:
            return queryset.filter(answer='')


@admin.register(models.Clarification)
class ClarificationAdmin(admin.ModelAdmin, JQueryModelAdmin):
    form = make_ajax_form(models.Clarification, {
        'contest': 'contests',
        'user': 'users',
    })

    def get_fields(self, request, obj=None):
        fields = ('contest', 'user', 'question', 'answer', 'format')
        if obj is not None:
            fields += (
                self.readonly_fields,
            )
        return fields

    readonly_fields = ('created_at', 'updated_at')
    list_display = ('__str__', 'has_answer', 'contest', 'user')
    list_filter = [ClarificationAnswerFilter]
    list_per_page = 30
    date_hierarchy = 'created_at'
    search_fields = ('contest__id', 'contest__name', 'question', 'user__username', 'user__login')

    def save_model(self, request, clarification, form, change):
        super().save_model(request, clarification, form, change)
        if not change:
            # A new clarification has been posted via the admin interface.
            notify_admins_about_clarification(request, clarification)
        elif clarification.has_answer():
            clear_clarification_messages(clarification)
            notify_user_about_clarification(request, clarification)

    def delete_model(self, request, clarification):
        clear_clarification_messages(clarification)
        super().delete_model(request, clarification)
