import abc
import collections
import itertools

from core.models    import ProblemInContest
from misc.itertools import indexed_groupby
from users.models   import User


class StandingsRow:
    def __init__(self, user_id, problem_count):
        self.user_id = user_id
        self.attempts = [None] * problem_count
        self.extras = collections.OrderedDict()


class BaseStandingsBuilder(abc.ABC):
    def __init__(self, contest):
        self.contest = contest

    @abc.abstractmethod
    def generate_attempts(self):
        pass

    def get_row_aggregators(self):
        return [ ]

    def get_column_aggregators(self):
        return [ ]

    def get_other_aggregators(self):
        return [ ]

    def postprocess_row_aggregations(self, odict):
        pass

    def postprocess_column_aggregations(self, odict):
        pass

    def postprocess_other_aggregations(self, odict):
        pass

    @abc.abstractmethod
    def get_ordering(self, row):
        pass

    def get_extra_ordering(self, row):
        return ()

    def get_total_ordering(self, row):
        return self.get_ordering(row) + self.get_extra_ordering(row)

    def build_table(self, aggregators):
        table = { }
        for attempt in self.generate_attempts():
            row = table.get(attempt.user_id)
            if row is None:
                table[attempt.user_id] = row = StandingsRow(attempt.user_id, len(self.pics))
            row.attempts[attempt.problem_number] = attempt
            for agtor in aggregators:
                agtor.update(attempt)

        return table

    def build(self):
        self.pics = list(
            ProblemInContest
            .objects
            .filter(contest=self.contest)
            .select_related('problem', 'contest')
            .order_by('number')
            .only('number', 'score', 'problem__name', 'contest__is_training')
        )
        row_aggregators    = self.get_row_aggregators()
        column_aggregators = self.get_column_aggregators()
        other_aggregators  = self.get_other_aggregators()
        all_aggregators = [a[1] for a in itertools.chain(
            row_aggregators, column_aggregators, other_aggregators,
        )]
        table = self.build_table(all_aggregators)

        self.usernames = dict(
            User
            .objects
            .filter(id__in=table)
            .values_list('id', 'username')
        )
        for user_id, username in self.usernames.items():
            table[user_id].username = username

        extras = [a[0] for a in row_aggregators]
        for field_name, agtor in row_aggregators:
            for user_id, value in agtor.finalize().items():
                table[user_id].extras[field_name] = value

        table = sorted(table.values(), key=self.get_total_ordering)
        for i, j, k, g in indexed_groupby(table, self.get_ordering, start=1):
            if i + 1 == j:
                g[0].rank = str(i)
            else:
                rank = '%d-%d' % (i, j - 1)
                for row in g:
                    row.rank = rank

        column_aggregations = collections.OrderedDict(
            [(name, agtor.finalize()) for name, agtor in column_aggregators]
        )
        other_aggregations = collections.OrderedDict(
            [(name, agtor.finalize()) for name, agtor in other_aggregators]
        )
        for row in table:
            self.postprocess_row_aggregations(row.extras)
        self.postprocess_column_aggregations(column_aggregations)
        self.postprocess_other_aggregations(other_aggregations)

        return self.pics, table, extras, column_aggregations, other_aggregations
