from ajax_select    import make_ajax_form
from django.contrib import admin

from jquery_model_admin import JQueryModelAdmin

from .models import News

@admin.register(News)
class NewsAdmin(admin.ModelAdmin, JQueryModelAdmin):
    form = make_ajax_form(
        News, {
            "user": "users",
        }
    )

    def get_fields(self, request, obj=None):
        fields = ("title", "description", "user", "visible")
        if obj is not None:
            fields += (
                self.readonly_fields,
            )
        return fields

    readonly_fields = ("created_at", "updated_at")
    list_display = ("id", "title", "user", "visible", "created_at")
    list_display_links = ("id", "title")
    list_filter = ("visible", "created_at")
    date_hierarchy = "created_at"
    search_fields = ("title", "user__login", "user__username", "user__email")
