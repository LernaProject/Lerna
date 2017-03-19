from django.db    import models as md
from django.urls  import reverse
from users.models import User


class News(md.Model):
    title       = md.CharField(max_length=255)
    description = md.TextField()
    user        = md.ForeignKey(User, md.PROTECT, db_index=False)
    created_at  = md.DateTimeField(auto_now_add=True)
    updated_at  = md.DateTimeField(auto_now=True)
    visible     = md.BooleanField(default=True)

    class Meta:
        db_table            = 'news'
        get_latest_by       = 'created_at'
        verbose_name_plural = 'news'

    @property
    def short_description(self):
        return self.description.partition('<more>')[0]

    @property
    def has_long_description(self):
        return '<more>' in self.description

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('news:show', args=[self.id])
