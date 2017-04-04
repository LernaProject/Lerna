from django.db import connection

from .base             import BaseStandingsBuilder
from ..aggregators     import ScoreRowAggregator
from ..attempt_results import KirovTrainingAttemptResult


class KirovTrainingStandingsBuilder(BaseStandingsBuilder):
    def generate_attempts(self):
        with connection.cursor() as cursor:
            # FIXME(nickolas): It's a hellish bottleneck to do this without a `LIMIT`.
            cursor.execute("""
                SELECT a.user_id, pic.number - 1, MAX(a.score) * .01
                FROM attempts a
                JOIN problem_in_contests pic ON pic.id = a.problem_in_contest_id
                WHERE pic.contest_id = %s
                AND a.result = 'Tested'
                GROUP BY a.user_id, pic.number
            """, [self.contest.id])

            for user_id, problem_number, score in cursor:
                yield KirovTrainingAttemptResult(user_id, problem_number, score)

    def get_row_aggregators(self):
        return [('score', ScoreRowAggregator([pic.score for pic in self.pics]))]

    def postprocess_row_aggregations(self, odict):
        odict['score'] = '%.2f' % odict['score']

    def get_ordering(self, row):
        return (-row.extras['score'], )

    def get_extra_ordering(self, row):
        return (row.username, row.user_id)
