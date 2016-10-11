from django.contrib           import admin
from django.utils.translation import ugettext as _

from .. import models


@admin.register(models.Compiler)
class CompilerAdmin(admin.ModelAdmin):
    def get_fields(self, request, obj=None):
        fields = ('name', 'code_name', 'extension', 'compile_string')
        if obj is not None:
            fields += (
                self.readonly_fields,
            )
        return fields

    readonly_fields = ('created_at', 'updated_at')
    list_display = ('name', 'code_name', 'extension')
    list_display_links = ('name', 'code_name')
    # list_filter = ['extension']
    ordering = ['id']
    # search_fields = ('name', 'code_name', 'extension')
