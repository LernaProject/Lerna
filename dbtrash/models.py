from django.db import models as md


class ActiveAdminComments(md.Model):
    namespace     = md.CharField(max_length=255)
    body          = md.TextField()
    resource_id   = md.CharField(max_length=255)
    resource_type = md.CharField(max_length=255)
    author_id     = md.IntegerField()
    author_type   = md.CharField(max_length=255)
    created_at    = md.DateTimeField(auto_now_add=True)
    updated_at    = md.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'active_admin_comments'


class CkeditorAssets(md.Model):
    data_file_name    = md.CharField(max_length=255)
    data_content_type = md.CharField(max_length=255, blank=True, null=True)
    data_file_size    = md.IntegerField(blank=True, null=True)
    assetable_id      = md.IntegerField(blank=True, null=True)
    assetable_type    = md.CharField(max_length=30, blank=True, null=True)
    type              = md.CharField(max_length=30, blank=True, null=True)
    width             = md.IntegerField(blank=True, null=True)
    height            = md.IntegerField(blank=True, null=True)
    created_at        = md.DateTimeField(auto_now_add=True)
    updated_at        = md.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ckeditor_assets'


class SchemaMigrations(md.Model):
    version = md.CharField(unique=True, max_length=255)

    class Meta:
        db_table = 'schema_migrations'


class UserSessions(md.Model):
    created_at = md.DateTimeField(auto_now_add=True)
    updated_at = md.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_sessions'
