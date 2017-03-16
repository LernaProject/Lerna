from django.contrib           import admin
from django.utils.translation import ugettext as _

from .. import models


@admin.register(models.Compiler)
class CompilerAdmin(admin.ModelAdmin):
    def actual(self, compiler):
        return not compiler.obsolete

    actual.boolean = True
    actual.admin_order_field = 'obsolete'

    def get_fields(self, request, obj=None):
        fields = ('name', 'codename', 'runner_codename', 'highlighter', 'extension', 'obsolete')
        if obj is not None:
            fields += (
                self.readonly_fields,
            )
        return fields

    readonly_fields = ('created_at', 'updated_at')
    list_display = ('name', 'codename', 'runner_codename', 'actual')
    list_display_links = ('name', 'codename')
    list_filter = ('runner_codename', 'obsolete')
    ordering = ['id']
    save_as = True
    save_as_continue = False
    search_fields = ('name', 'codename', 'runner_codename')
