from ajax_select              import make_ajax_form
from ajax_select.admin        import AjaxSelectAdminTabularInline
from django.contrib           import admin
from django.utils.translation import ugettext as _

from jquery_model_admin import JQueryModelAdmin

from .. import models


# TODO: Put a constraint on problem numbers (must be unique, consecutive and start from 1).
class ProblemInContestInline(AjaxSelectAdminTabularInline):
    model = models.ProblemInContest
    form = make_ajax_form(
        model, {
            "problem": "problems",
        }
    )
    fields = ("number", "problem", "score")
    ordering = ["number"]

    def get_extra(self, request, obj=None, **kwargs):
        extra = 8
        return extra if obj is None else max(extra - obj.problem_count, 0)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("problem", "contest")


@admin.register(models.Contest)
class ContestAdmin(admin.ModelAdmin, JQueryModelAdmin):
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
