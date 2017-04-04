from django.db import connection

from core.util         import format_time
from .base             import BaseStandingsBuilder
from .util             import LastAttemptsMixin
from ..aggregators     import *
from ..attempt_results import TimedKirovAttemptResult


class KirovStandingsBuilder(LastAttemptsMixin, BaseStandingsBuilder):
    def __init__(self, contest, unfrozen):
        super().__init__(contest)
        self.unfrozen = unfrozen

    def generate_attempts(self):
        with connection.cursor() as cursor:
            cursor.execute("""
                WITH all_attempts AS (
                    SELECT a.user_id, pic.number AS num, a.time, a.score
                    FROM attempts a
                    JOIN problem_in_contests pic ON pic.id = a.problem_in_contest_id
                    WHERE pic.contest_id = %s
                    AND a.result = 'Tested'
                    AND a.time < %s
                )
                SELECT a.user_id, a.num - 1, COUNT(*), best.time, best.score * .01
                FROM all_attempts a
                JOIN (
                    SELECT DISTINCT ON (user_id, num) *
                    FROM all_attempts
                    ORDER BY user_id, num, score DESC, "time"
                ) best ON best.user_id = a.user_id AND best.num = a.num
                WHERE a.time <= best.time
                GROUP BY a.user_id, a.num, best.time, best.score
            """, [self.contest.id, self.contest.get_due_time(self.unfrozen)])

            start_time = self.contest.start_time
            for user_id, problem_number, attempt_count, time, score in cursor:
                yield TimedKirovAttemptResult(
                    user_id, problem_number, score, attempt_count, time, start_time)

    def get_row_aggregators(self):
        return [
            ('score',   ScoreRowAggregator([pic.score for pic in self.pics])),
            ('penalty', PenaltyTimeRowAggregator()),
        ]

    def get_column_aggregators(self):
        count = len(self.pics)
        return [
            ('total_runs',     TotalAttemptsColumnAggregator(count)),
            ('full',           AcceptedAttemptsColumnAggregator(count)),
            ('total_score',    TotalScoreColumnAggregator(count)),
            ('first_accepted', FirstAcceptedColumnAggregator(count)),
            ('last_accepted',  LastAcceptedColumnAggregator(count)),
        ]

    def postprocess_row_aggregations(self, odict):
        odict['score'] = '%.2f' % odict['score']

    def postprocess_column_aggregations(self, odict):
        total_scores = odict['total_score']
        for i, value in enumerate(total_scores):
            value = '%.1f' % value
            total_scores[i] = value[:-2] if value[-1] == '0' else value

        for key in ('first_accepted', 'last_accepted'):
            values = odict[key]
            for i, attempt in enumerate(values):
                if attempt is not None:
                    values[i] = format_time(attempt.minutes)

    def get_ordering(self, row):
        return (-row.extras['score'], row.extras['penalty'])

    def get_extra_ordering(self, row):
        return (row.username, row.user_id)
