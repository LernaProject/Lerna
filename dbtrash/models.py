from django.db import models


class ActiveAdminComments(models.Model):
    namespace     = models.CharField(max_length=255)
    body          = models.TextField()
    resource_id   = models.CharField(max_length=255)
    resource_type = models.CharField(max_length=255)
    author_id     = models.IntegerField()
    author_type   = models.CharField(max_length=255)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'active_admin_comments'


class CkeditorAssets(models.Model):
    data_file_name    = models.CharField(max_length=255)
    data_content_type = models.CharField(max_length=255, blank=True, null=True)
    data_file_size    = models.IntegerField(blank=True, null=True)
    assetable_id      = models.IntegerField(blank=True, null=True)
    assetable_type    = models.CharField(max_length=30, blank=True, null=True)
    type              = models.CharField(max_length=30, blank=True, null=True)
    width             = models.IntegerField(blank=True, null=True)
    height            = models.IntegerField(blank=True, null=True)
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ckeditor_assets'


class SchemaMigrations(models.Model):
    version = models.CharField(unique=True, max_length=255)

    class Meta:
        db_table = 'schema_migrations'


class UserSessions(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_sessions'
