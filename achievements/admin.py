from ajax_select    import make_ajax_form
from django.contrib import admin

from jquery_model_admin import JQueryModelAdmin

from .models import Achievement, UserAchievement

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin, JQueryModelAdmin):
    def get_fields(self, request, obj=None):
        fields = ('name', 'description', 'points', 'icon_path', 'amount', 'problem', 'contest', 'author', 'origin',
                  'language')
        if obj is not None:
            fields += (
                self.readonly_fields,
            )
        return fields

    readonly_fields = ('created_at', 'updated_at')
    list_display = ('id', 'name', 'description', 'points', 'icon_path', 'created_at')
    list_display_links = ('id', 'name')
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'
    search_fields = ('name', 'points')

@admin.register(UserAchievement)
class NewsAdmin(admin.ModelAdmin, JQueryModelAdmin):
    form = make_ajax_form(UserAchievement, {
        'user': 'users',
        'achievement': 'achievements'
    })

    def get_fields(self, request, obj=None):
        fields = ('user', 'achievement', 'earned_at')
        if obj is not None:
            fields += (
                self.readonly_fields,
            )
        return fields

    readonly_fields = ('created_at', 'updated_at')
    list_display = ('id', 'user', 'achievement', 'earned_at', 'created_at')
    list_display_links = ('id',)
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'
    search_fields = ('achievement__name', 'user__login', 'user__username', 'user__email')