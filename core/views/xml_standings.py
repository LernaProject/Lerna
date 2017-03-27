import io
import uuid
from   xml.sax import saxutils

from django.db.models             import F, Func, CharField, BigIntegerField
from django.db.models.expressions import RawSQL
from django.db.models.functions   import Cast
from django.http                  import HttpResponse, Http404
from django.utils                 import timezone
from django.views.generic         import View

from .util import (
    SelectContestMixin, StandingsDueTimeMixinABC, StandingsDueTimeMixin,
    UnfrozenStandingsDueTimeMixin,
)
from core.models import Attempt, ProblemInContest


class BaseXMLStandingsView(StandingsDueTimeMixinABC, SelectContestMixin, View):
    @staticmethod
    def _encode_datetime(moment):
        return timezone.localtime(moment).strftime('%Y/%m/%d %H:%M:%S').encode()

    # TODO: use is_staff mixin instead, when it is ready
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise Http404('Не существует запрошенной страницы')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, contest_id, *args, **kwargs):
        contest = self.select_contest()
        if contest.is_training:
            raise Http404
        pics = list(
            ProblemInContest
            .objects
            .filter(contest=contest_id)
            .annotate(letter=Func(
                # ord('A') - 1 == 64
                F('number') + 64,
                function='chr',
                output_field=CharField(),
            ))
            .order_by('number')
            .values_list('id', 'letter', 'problem__name')
        )
        attempts = (
            Attempt
            .objects
            .filter(
                problem_in_contest__in=[pic_id for pic_id, letter, name in pics],
                time__lt=self.get_due_time(contest),
            )
            .annotate(
                submit_time_sec=RawSQL('extract(epoch FROM time - %s)', [contest.start_time]),
                time_ns=Cast(F('used_time') * 1000000000 + 0.5, BigIntegerField()),
            )
            # .order_by('time')
            .values_list(
                'id', 'submit_time_sec', 'result', 'score', 'time_ns',
                'user', 'user__username',
                'problem_in_contest',
                'compiler', 'compiler__codename', 'compiler__name',
            )
        )
        users = { }
        compilers = { }
        a = io.BytesIO()
        # We generate XML "by hand" for extra speed.
        for (attempt_id, submit_time_sec, result, score, time_ns, user_id, username, pic_id,
            compiler_id, codename, compiler_name) in attempts:

            users[user_id] = username
            compilers[compiler_id] = (codename, compiler_name)
            status, test = Attempt.encode_ejudge_verdict(result, score)
            a.write(
                b'<run run_id="%d" time="%d"'
                b' user_id="%d" prob_id="%d" lang_id="%d" status="%s" test="%d"'
                b' nsec="%d" run_uuid="%s" passed_mode="yes"/>' % (
                    attempt_id, submit_time_sec,
                    user_id, pic_id, compiler_id, status, test,
                    time_ns or 0, str(uuid.uuid4()).encode(),
                )
            )

        r = HttpResponse(content_type='application/xml')
        r.write(
            b'<?xml version="1.0" encoding="utf-8"?>'
            b'<runlog contest_id="%s" duration="%d" fog_time="%d"'
            b' start_time="%s" stop_time="%s" current_time="%s">'
            b'<name>%s</name>'
            b'<users>' % (
                contest_id.encode(),
                contest.duration * 60,
                contest.freezing_time * 60,
                self._encode_datetime(contest.start_time),
                self._encode_datetime(contest.finish_time),
                self._encode_datetime(timezone.now()),
                saxutils.escape(contest.name).encode(),
            )
        )
        for user_id, username in users.items():
            r.write(b'<user id="%d" name=%s/>' % (user_id, saxutils.quoteattr(username).encode()))
        r.write(b'</users><problems>')
        for pic_id, letter, name in pics:
            r.write(b'<problem id="%d" short_name="%c" long_name=%s/>' % (
                pic_id, letter.encode(), saxutils.quoteattr(name).encode(),
            ))
        r.write(b'</problems><languages>')
        for compiler_id, (codename, name) in compilers.items():
            r.write(
                b'<language id="%d" short_name=%s long_name=%s/>' % (
                compiler_id,
                saxutils.quoteattr(codename).encode(),
                saxutils.quoteattr(name).encode(),
            ))
        r.write(b'</languages><runs>')
        r.write(a.getvalue())
        r.write(b'</runs></runlog>')
        return r


class XMLStandingsView(StandingsDueTimeMixin, BaseXMLStandingsView):
    pass


class UnfrozenXMLStandingsView(UnfrozenStandingsDueTimeMixin, BaseXMLStandingsView):
    pass
