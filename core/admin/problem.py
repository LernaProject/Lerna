from django.contrib           import admin
from django.utils.translation import ugettext as _

from .. import models


@admin.register(models.Problem)
class ProblemAdmin(admin.ModelAdmin):
    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            (
                None, {
                    'fields': (
                        'name', ('author', 'developer'), 'origin', ('time_limit', 'memory_limit'),
                        # Current tester implementation doesn't support file I/O for solutions.
                        # ('input_file', 'output_file'),
                    ),
                }
            ), (
                _('Testing'), {
                    'fields': ('path', 'mask_in', 'mask_out', 'checker'),
                }
            ), (
                _('Description'), {
                    'fields': (
                        'description',
                        'input_specification', 'output_specification',
                        'samples', 'explanations',
                        'notes',
                    ),
                    'classes': ['collapse'],
                }
            ), (
                _('Analysis'), {
                    'fields': ['analysis'],
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

    readonly_fields = ('created_at', 'updated_at')
    list_display = ('id', 'name', 'path', 'mask_in', 'mask_out', 'checker')
    list_display_links = ('id', 'name')
    list_filter = ('created_at', 'checker', 'origin')
    date_hierarchy = 'created_at'
    search_fields = ('name', 'author', 'developer', 'path')
