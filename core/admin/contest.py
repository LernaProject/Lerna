from django.contrib           import admin
from django.utils.translation import ugettext as _

import ajax_select

from jquery_model_admin import JQueryModelAdmin

from .. import models


# TODO(nickolas): Put a constraint on problem numbers (must be unique, consecutive, and 1-based).
class ProblemInContestInline(ajax_select.admin.AjaxSelectAdminTabularInline):
    model = models.ProblemInContest
    form = ajax_select.make_ajax_form(
        model, {
            'problem': 'problems',
        }
    )
    fields = ('number', 'problem', 'score')
    ordering = ['number']

    def get_extra(self, request, obj=None, **kwargs):
        return 8 if obj is None else max(8 - obj.problem_count, 0)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('problem', 'contest')


class UserInContestInline(ajax_select.admin.AjaxSelectAdminTabularInline):
    model = models.UserInContest
    form = ajax_select.make_ajax_form(
        model, {
            'user': 'users',
        }
    )
    fields = ('user', 'contest')
    ordering = ['user']
    extra = 0

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'contest')


@admin.register(models.Contest)
class ContestAdmin(admin.ModelAdmin, JQueryModelAdmin):
    def get_fields(self, request, obj=None):
        fields = (
            'name', 'description',
            ('duration', 'freezing_time'),
            'start_time',
            ('is_school', 'is_admin', 'is_training', 'is_registration_required'),
        )
        if obj is not None:
            fields += (
                self.readonly_fields,
            )
        return fields

    readonly_fields = ('created_at', 'updated_at')
    inlines = [ProblemInContestInline, UserInContestInline]
    list_display = (
        'id', 'name', 'problem_count', 'duration', 'freezing_time', 'start_time',
        'is_school', 'is_admin', 'is_training', 'is_registration_required',
    )
    list_display_links = ('id', 'name')
    list_per_page = 30
    list_filter = ('is_school', 'is_admin', 'is_training', 'is_registration_required')
    date_hierarchy = 'start_time'
    search_fields = ('name', 'problems__name')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['duration'].initial = '300'
        form.base_fields['freezing_time'].initial = '240'
        return form

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('problem_in_contest_set')
