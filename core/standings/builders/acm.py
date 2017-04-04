from django.db import connection

from core.util         import format_time
from .base             import BaseStandingsBuilder
from .util             import LastAttemptsMixin
from ..aggregators     import *
from ..attempt_results import TimedAcmAttemptResult


class AcmStandingsBuilder(LastAttemptsMixin, BaseStandingsBuilder):
    def __init__(self, contest, unfrozen):
        super().__init__(contest)
        self.unfrozen = unfrozen

    def generate_attempts(self):
        with connection.cursor() as cursor:
            cursor.execute("""
                WITH all_attempts AS (
                    SELECT a.user_id, pic.number AS num, a.time, a.result = 'Accepted' AS succeeded
                    FROM attempts a
                    JOIN problem_in_contests pic ON pic.id = a.problem_in_contest_id
                    WHERE pic.contest_id = %s
                    AND a.result NOT IN ('', 'Queued', 'Compiling...', 'Compilation error', 'Ignored')
                    AND a.result NOT LIKE 'Testing%%'
                    AND a.result NOT LIKE 'System error%%'
                    AND a.time < %s
                )
                SELECT a.user_id, a.num - 1, COUNT(*), MAX(a.time), ok.user_id IS NOT NULL
                FROM all_attempts a
                LEFT JOIN (
                    SELECT user_id, num, MIN("time") AS succeeded_at
                    FROM all_attempts
                    WHERE succeeded
                    GROUP BY user_id, num
                ) ok ON ok.user_id = a.user_id AND ok.num = a.num
                WHERE ok.succeeded_at IS NULL
                OR a.time <= ok.succeeded_at
                GROUP BY a.user_id, a.num, ok.user_id
            """, [self.contest.id, self.contest.get_due_time(self.unfrozen)])

            start_time = self.contest.start_time
            for user_id, problem_number, attempt_count, time, succeeded in cursor:
                yield TimedAcmAttemptResult(
                    user_id, problem_number, succeeded, attempt_count, time, start_time)

    def get_row_aggregators(self):
        return [
            ('solved',  AcceptedCountRowAggregator()),
            ('penalty', PenaltyTimeRowAggregator()),
        ]

    def get_column_aggregators(self):
        count = len(self.pics)
        return [
            ('total_runs',     TotalAttemptsColumnAggregator(count)),
            ('accepted',       AcceptedAttemptsColumnAggregator(count)),
            ('rejected',       NonAcceptedAttemptsColumnAggregator(count)),
            ('first_accepted', FirstAcceptedColumnAggregator(count)),
            ('last_accepted',  LastAcceptedColumnAggregator(count)),
        ]

    def postprocess_column_aggregations(self, odict):
        for key in ('first_accepted', 'last_accepted'):
            values = odict[key]
            for i, attempt in enumerate(values):
                if attempt is not None:
                    values[i] = format_time(attempt.minutes)

    def get_ordering(self, row):
        return (-row.extras['solved'], row.extras['penalty'])

    def get_extra_ordering(self, row):
        return (row.username, row.user_id)
