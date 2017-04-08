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
                        'statements_format',
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

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['time_limit'].initial = '1000'
        form.base_fields['memory_limit'].initial = '64'
        # Polygon default masks.
        form.base_fields['mask_in'].initial = '%02d'
        form.base_fields['mask_out'].initial = '%02d.a'
        form.base_fields['samples'].initial = (
            '|_. Стандартный ввод |_. Стандартный вывод |\n'
            '|Input1\n'
            '|Output1|\n'
            '|Input2\n'
            '|Output2|'
        )
        return form

    readonly_fields = ('created_at', 'updated_at')
    list_display = ('id', 'name', 'path', 'mask_in', 'mask_out', 'checker')
    list_display_links = ('id', 'name')
    list_filter = ('created_at', 'checker', 'origin')
    date_hierarchy = 'created_at'
    search_fields = ('name', 'author', 'developer', 'path')
