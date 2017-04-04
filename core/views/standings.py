from django.http          import Http404
from django.views.generic import TemplateView

from core.standings.builders import (
    AcmStandingsBuilder, AcmTrainingStandingsBuilder,
    KirovStandingsBuilder, # TODO: KirovTrainingStandingsBuilder.
)
from .util import NotificationListMixin, SelectContestMixin, get_relative_time_info


class StandingsView(SelectContestMixin, NotificationListMixin, TemplateView):
    template_name = 'contests/rating.html'
    unfrozen = False

    def get_context_data(self, **kwargs):
        contest = self.select_contest()
        time_info = get_relative_time_info(contest)
        if contest.is_school:
            if contest.is_training:
                raise NotImplementedError
            else:
                builder = KirovStandingsBuilder(contest, self.unfrozen)
        elif contest.is_training:
            builder = AcmTrainingStandingsBuilder(contest)
        else:
            builder = AcmStandingsBuilder(contest, self.unfrozen)

        pics, standings, extras, statistics, summary = builder.build()
        context = super().get_context_data(**kwargs)
        context.update(
            contest=contest,
            time_info=time_info,
            available=contest.is_available_for(self.request.user),
            notifications=self.get_notifications(contest),
            problems=pics,
            extras=extras,
            summary=summary,
            standings=standings,
            statistics=statistics,
        )
        return context


class UnfrozenStandingsView(StandingsView):
    unfrozen = True

    # TODO: use is_staff mixin instead, when it is ready
    def dispath(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise Http404('Не существует запрошенной страницы')
        return super().dispath(request, *args, **kwargs)
