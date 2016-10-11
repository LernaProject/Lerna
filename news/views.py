from django.shortcuts import get_object_or_404, render
from django.views     import generic

from .models import News


class IndexView(generic.ListView):
    model = News
    ordering = '-created_at'
    template_name = 'news/index.html'
    allow_empty = True
    paginate_by = 5
    paginate_orphans = 1


class DetailView(generic.DetailView):
    model = News
    template_name = 'news/show.html'
