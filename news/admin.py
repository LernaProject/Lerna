from django.contrib import admin

from .models import News

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        return ("created_at", "updated_at") if obj is not None else ()

    raw_id_fields = ["user"]
    list_display = ("id", "title", "visible", "created_at")
    list_display_links = ("id", "title")
    list_filter = ("visible", "created_at")
    search_fields = ("title", "user__login", "user__username", "user__email")
    date_hierarchy = "created_at"
