from django.contrib           import admin
from django.utils.translation import ugettext as _

from .. import models


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
