from django.contrib           import admin
from django.utils.translation import ugettext as _

from .models import Compiler, Problem

@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            (
                None, {
                    "fields": (
                        "name", "author", "developer", "origin",
                        ("time_limit", "memory_limit"),
                        "input_file", "output_file",
                    ),
                },
            ), (
                _("Testing"), {
                    "fields": ("path", "mask_in", "mask_out", "checker"),
                },
            ), (
                _("Description"), {
                    "fields": (
                        "description",
                        "input_specification", "output_specification",
                        "samples", "explanations",
                        "notes",
                    ),
                    "classes": ["collapse"],
                },
            ), (
                _("Analysis"), {
                    "fields": ["analysis"],
                    "classes": ["collapse"],
                },
            ),
        )
        if obj is not None:
            fieldsets += (
                (
                    _("Statistics"), {
                        "fields": ("created_at", "updated_at"),
                    },
                ),
            )
        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        return ("created_at", "updated_at") if obj is not None else ()

    list_display = ("id", "name", "path", "mask_in", "mask_out", "checker")
    list_display_links = ("id", "name")
    list_filter = ("created_at", "checker", "origin")
    search_fields = ("name", "author", "developer", "path")
    date_hierarchy = "created_at"

@admin.register(Compiler)
class CompilerAdmin(admin.ModelAdmin):
    list_display = ("name", "code_name", "extension")
    list_display_links = ("name", "code_name")
    # list_filter = ["extension"]
    ordering = ["id"]
    # search_fields = ("name", "code_name", "extension")

    def get_readonly_fields(self, request, obj=None):
        return ("created_at", "updated_at") if obj is not None else ()
