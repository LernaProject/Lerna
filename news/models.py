from django.db    import models
from users.models import User

class News(models.Model):
    title       = models.CharField(max_length=255)
    description = models.TextField()
    user        = models.ForeignKey(User, db_index=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    visible     = models.BooleanField(default=True)

    class Meta:
        db_table            = 'news'
        get_latest_by       = 'created_at'
        verbose_name_plural = 'news'

    def __str__(self):
        return self.title
