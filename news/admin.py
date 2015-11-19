from django.contrib import admin

from .models import News

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    def get_fields(self, request, obj=None):
        fields = ("title", "description", "user", "visible")
        if obj is not None:
            fields += (
                self.readonly_fields,
            )
        return fields

    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ["user"]
    list_display = ("id", "title", "user", "visible", "created_at")
    list_display_links = ("id", "title")
    list_filter = ("visible", "created_at")
    date_hierarchy = "created_at"
    search_fields = ("title", "user__login", "user__username", "user__email")
