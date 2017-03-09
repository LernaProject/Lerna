from ajax_select              import make_ajax_form
from django                   import db, forms
from django.contrib           import admin
from django.utils.translation import ugettext as _

from jquery_model_admin import JQueryModelAdmin

from .. import models


class TestInfoInline(admin.TabularInline):
    model = models.TestInfo
    fields = ('test_number', 'result', 'used_time', 'used_memory', 'checker_comment')
    ordering = ['test_number']
    formfield_overrides = {
        db.models.TextField: { 'widget': forms.TextInput },
    }
    extra = 0


@admin.register(models.Attempt)
class AttemptAdmin(admin.ModelAdmin, JQueryModelAdmin):
    form = make_ajax_form(
        models.Attempt, {
            'user': 'users',
            'problem_in_contest': 'problems_in_contests',
        }
    )

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            (
                None, {
                    'fields': ('user', 'problem_in_contest', 'compiler'),
                }
            ), (
                _('Source'), {
                    'fields': ('source', 'error_message'),
                    'classes': ['collapse'],
                }
            ), (
                _('Results'), {
                    'fields': (
                        ('result', 'score'),
                        ('used_time', 'used_memory'),
                        'tester_name',
                        'checker_comment',
                    ),
                }
            ), (
                _('Rails trash'), {
                    'fields': ['lock_version'],
                    'classes': ['collapse'],
                }
            ),
        )
        if obj is not None:
            fieldsets += (
                (
                    _('Statistics'), {
                        'fields': [self.readonly_fields],
                    }
                ),
            )
        return fieldsets

    readonly_fields = ('time', 'updated_at')

    def get_inline_instances(self, request, obj=None):
        if obj is None or obj.score is not None:
            return [TestInfoInline(self.model, self.admin_site)]
        else:
            return ()

    list_display = (
        'id', 'user', 'problem', 'compiler', 'contest', 'verdict', 'time',
        'used_time', 'used_memory',
    )
    list_display_links = ('id', 'user', 'problem')
    list_filter = ('runner_codename', 'obsolete')
    date_hierarchy = 'time'

    # actions = ()

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            'user', 'problem_in_contest__problem', 'problem_in_contest__contest',
        )
