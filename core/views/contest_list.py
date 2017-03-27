import os.path

from django.utils         import timezone
from django.views.generic import TemplateView

from core.models import Contest


class ContestIndexView(TemplateView):
    template_name = 'contests/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # FIXME(nickolas): `LIMIT`.
        contests = (
            Contest
            .objects
            .privileged(self.request.user)
            .filter(is_training=False)
            .order_by('-start_time', 'id')
        )

        for contest in contests:
            contest.available = contest.is_available_for(self.request.user)

        actual, awaiting, past = Contest.three_way_split(contests, timezone.now())
        actual.reverse()
        awaiting.reverse()

        context.update(
            actual_contest_list=actual,
            wait_contest_list=awaiting,
            past_contest_list=past,
        )
        return context


class TrainingIndexView(TemplateView):
    template_name = 'contests/trainings/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trainings_raw = (
            Contest
            .objects
            .privileged(self.request.user)
            .filter(is_training=True)
            .order_by('name')
        )

        trainings = []
        cur_prefixes = []

        for t in trainings_raw:
            name_parts = t.name.split('/')

            # BUG(nickolas): Calling os.path.commonprefix on a [[str]] is an undocumented feature.
            # NOTE: os.path.commonprefix(['/usr/lib', '/usr/local/lib']) == '/usr/l'
            cur_prefixes = os.path.commonprefix([name_parts, cur_prefixes])
            idx = len(cur_prefixes)

            while idx < len(name_parts):
                if idx == len(name_parts) - 1:
                    trainings.append({
                        'tab': ' ' * idx,
                        'is_terminal': True,
                        'id': t.id,
                        'name': name_parts[idx]
                    })
                else:
                    cur_prefixes.append(name_parts[idx])
                    trainings.append({
                        'tab': ' ' * idx,
                        'is_terminal': False,
                        'id': None,
                        'name': name_parts[idx]
                    })
                idx += 1

        context['trainings'] = trainings
        return context
