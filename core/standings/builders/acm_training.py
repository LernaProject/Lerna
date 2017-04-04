from django.db import connection

from .base             import BaseStandingsBuilder
from ..aggregators     import AcceptedCountRowAggregator
from ..attempt_results import AcmTrainingAttemptResult


class AcmTrainingStandingsBuilder(BaseStandingsBuilder):
    def generate_attempts(self):
        with connection.cursor() as cursor:
            # FIXME(nickolas): It's a hellish bottleneck to do this without a `LIMIT`.
            cursor.execute("""
                SELECT a.user_id, pic.number - 1, MIN(a.result) = 'Accepted'
                FROM attempts a
                JOIN problem_in_contests pic ON pic.id = a.problem_in_contest_id
                WHERE pic.contest_id = %s
                AND a.result NOT IN ('', 'Queued', 'Compiling...', 'Compilation error', 'Ignored')
                AND a.result NOT LIKE 'Testing%%'
                AND a.result NOT LIKE 'System error%%'
                GROUP BY a.user_id, pic.number
            """, [self.contest.id])

            for user_id, problem_number, succeeded in cursor:
                yield AcmTrainingAttemptResult(user_id, problem_number, succeeded)

    def get_row_aggregators(self):
        return [('solved', AcceptedCountRowAggregator())]

    def get_ordering(self, row):
        return (-row.extras['solved'], )

    def get_extra_ordering(self, row):
        return (row.username, row.user_id)
