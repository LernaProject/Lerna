from ajax_select              import make_ajax_form
from django.contrib           import admin
from django.utils.translation import ugettext as _

from jquery_model_admin import JQueryModelAdmin

from .. import models


@admin.register(models.Notification)
class NotificationAdmin(admin.ModelAdmin, JQueryModelAdmin):
    form = make_ajax_form(
        models.Notification, {
            'contest': 'contests',
        }
    )

    def get_fields(self, request, obj=None):
        fields = ('contest', 'description', 'visible')
        if obj is not None:
            fields += (
                self.readonly_fields,
            )
        return fields

    readonly_fields = ('created_at', 'updated_at')
    list_display = ('contest', '__str__', 'visible')
    list_display_links = ('contest', '__str__')
    list_per_page = 30
    date_hierarchy = 'created_at'
    search_fields = ('contest__name', 'description')
