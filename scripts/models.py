from django.db import models


class TesterStatus(models.Model):
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table      = 'checker_statuses'
        get_latest_by = 'updated_at'

    def __str__(self):
        return '#{0.id} ({0.updated_at})'.format(self)
