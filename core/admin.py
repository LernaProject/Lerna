from django.contrib           import admin
from django.utils.translation import ugettext as _

from . import models


@admin.register(models.Problem)
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
                }
            ), (
                _("Testing"), {
                    "fields": ("path", "mask_in", "mask_out", "checker"),
                }
            ), (
                _("Description"), {
                    "fields": (
                        "description",
                        "input_specification", "output_specification",
                        "samples", "explanations",
                        "notes",
                    ),
                    "classes": ["collapse"],
                }
            ), (
                _("Analysis"), {
                    "fields": ["analysis"],
                    "classes": ["collapse"],
                }
            ),
        )
        if obj is not None:
            fieldsets += (
                (
                    _("Statistics"), {
                        "fields": [self.readonly_fields],
                    }
                ),
            )
        return fieldsets

    readonly_fields = ("created_at", "updated_at")
    list_display = ("id", "name", "path", "mask_in", "mask_out", "checker")
    list_display_links = ("id", "name")
    list_filter = ("created_at", "checker", "origin")
    date_hierarchy = "created_at"
    search_fields = ("name", "author", "developer", "path")


# TODO: Put a constraint on problem numbers (must be unique, consecutive and start from 1).
class ProblemInContestInline(admin.TabularInline):
    model = models.ProblemInContest
    fields = ("number", "problem", "score")
    raw_id_fields = ["problem"]
    ordering = ["number"]

    def get_extra(self, request, obj=None, **kwargs):
        extra = 8
        return extra if obj is None else max(extra - obj.problem_count, 0)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("problem", "contest")


@admin.register(models.Contest)
class ContestAdmin(admin.ModelAdmin):
    def get_fields(self, request, obj=None):
        fields = (
            "name", "description",
            ("duration", "freezing_time"),
            "start_time",
            ("is_school", "is_admin", "is_training"),
        )
        if obj is not None:
            fields += (
                self.readonly_fields,
            )
        return fields

    readonly_fields = ("created_at", "updated_at")
    inlines = [ProblemInContestInline]
    list_display = (
        "id", "name", "problem_count", "duration", "freezing_time", "start_time",
        "is_school", "is_admin", "is_training",
    )
    list_display_links = ("id", "name")
    list_per_page = 30
    list_filter = ("is_school", "is_admin", "is_training")
    date_hierarchy = "start_time"
    search_fields = ("name", "problems__name")

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("problem_in_contest_set")


class ClarificationAnswerFilter(admin.SimpleListFilter):
    title = _("has answer")

    parameter_name = "has_answer"

    def lookups(self, request, model_admin):
        return (
            ("True", _("Yes")),
            ("False", _("No")),
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        elif self.value() == "True":
            return queryset.exclude(answer="")
        else:
            return queryset.filter(answer="")


@admin.register(models.Clarification)
class ClarificationAdmin(admin.ModelAdmin):
    def get_fields(self, request, obj=None):
        fields = ("contest", "user", "question", "answer")
        if obj is not None:
            fields += (
                self.readonly_fields,
            )
        return fields

    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("contest", "user")
    list_display = ("__str__", "has_answer", "contest", "user")
    list_filter = [ClarificationAnswerFilter]
    list_per_page = 30
    date_hierarchy = "created_at"
    search_fields = ("contest__name", "question", "user__username", "user__login")

@admin.register(models.Notification)
class NotificationAdmin(admin.ModelAdmin):
    def get_fields(self, request, obj=None):
        fields = ("contest", "description", "visible")
        if obj is not None:
            fields += (
                self.readonly_fields,
            )
        return fields

    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ["contest"]
    list_display = ("contest", "__str__", "visible")
    list_display_links = ("contest", "__str__")
    list_per_page = 30
    date_hierarchy = "created_at"
    search_fields = ("contest__name", "description")

@admin.register(models.Compiler)
class CompilerAdmin(admin.ModelAdmin):
    def get_fields(self, request, obj=None):
        fields = ("name", "code_name", "extension", "compile_string")
        if obj is not None:
            fields += (
                self.readonly_fields,
            )
        return fields

    readonly_fields = ("created_at", "updated_at")
    list_display = ("name", "code_name", "extension")
    list_display_links = ("name", "code_name")
    # list_filter = ["extension"]
    ordering = ["id"]
    # search_fields = ("name", "code_name", "extension")
