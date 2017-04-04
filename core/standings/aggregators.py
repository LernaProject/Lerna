"""
An aggregator can be used to collect some kind of statistics for a contest. An
aggregator is first fed with attempts via its `update` method, and then results
can be acquired with a call to `finalize`. It is forbidden to `update` a
`finalize`d aggregator. Aggregators may (but are not required to) support
calling `finalize` more than once.

There are three types of aggregators: common (e.g., the last submitted attempt),
row-based (participant's penalty time), and column-based (number of rejected
attempts for a problem). For now, it is impossible to perform a row aggregation
on results of a column aggregation, or vice versa.

For a common aggregator, `finalize` may return anything it thinks would be
appropriate, even `None`.

For a row-based aggregator, `finalize` should return a dict-like object mapping
participant IDs to calculated values. That dict must contain an entry for each
ID ever used to populate the aggregator.

For a column-based aggregator, `finalize` should return a (reenterable) iterable
of length exactly `problem_count` containing results of an aggregation.
"""

import abc
import collections


class Aggregator(abc.ABC):
    @abc.abstractmethod
    def update(self, attempt):
        pass

    def finalize(self):
        self.update = None


class _ResultMixin:
    def finalize(self):
        super().finalize()
        return self.result


# Common aggregators.

class BestAttemptAggregator(_ResultMixin, Aggregator):
    def __init__(self):
        self.result = None

    def update(self, attempt):
        if self.check(attempt, self.result):
            self.result = attempt

    @abc.abstractmethod
    def check(self, candidate, best):
        pass


class LastSubmittedAggregator(BestAttemptAggregator):
    @staticmethod
    def check(candidate, best):
        return best is None or candidate.time > best.time


class LastAcceptedAggregator(LastSubmittedAggregator):
    @classmethod
    def check(cls, candidate, best):
        return candidate.accepted and super().check(candidate, best)


# Row-based aggregators.

class AcceptedCountRowAggregator(_ResultMixin, Aggregator):
    def __init__(self):
        self.result = collections.defaultdict(lambda: 0)

    def update(self, attempt):
        if attempt.accepted:
            self.result[attempt.user_id] += 1
        else:
            self.result[attempt.user_id]


class ScoreRowAggregator(_ResultMixin, Aggregator):
    def __init__(self, scores):
        self.scores = scores
        self.result = collections.defaultdict(lambda: 0)

    def update(self, attempt):
        if not attempt.rejected:
            self.result[attempt.user_id] += attempt.score * self.scores[attempt.problem_number]
        else:
            self.result[attempt.user_id]


class PenaltyTimeRowAggregator(_ResultMixin, Aggregator):
    def __init__(self, penalty=20):
        self.result = collections.defaultdict(lambda: 0)
        self.penalty = penalty

    def update(self, attempt):
        if not attempt.rejected:
            self.result[attempt.user_id] += self.calculate_penalty(attempt)
        else:
            self.result[attempt.user_id]

    def calculate_penalty(self, attempt):
        return attempt.minutes + (attempt.count - 1) * self.penalty


# Column-based aggregators.

class TotalAttemptsColumnAggregator(_ResultMixin, Aggregator):
    def __init__(self, problem_count):
        self.result = [0] * problem_count

    def update(self, attempt):
        self.result[attempt.problem_number] += attempt.count


class AcceptedAttemptsColumnAggregator(_ResultMixin, Aggregator):
    def __init__(self, problem_count):
        self.result = [0] * problem_count

    def update(self, attempt):
        if attempt.accepted:
            self.result[attempt.problem_number] += 1


class NonAcceptedAttemptsColumnAggregator(_ResultMixin, Aggregator):
    def __init__(self, problem_count):
        self.result = [0] * problem_count

    def update(self, attempt):
        self.result[attempt.problem_number] += attempt.count - attempt.accepted


class TotalScoreColumnAggregator(_ResultMixin, Aggregator):
    def __init__(self, problem_count):
        self.result = [0] * problem_count

    def update(self, attempt):
        self.result[attempt.problem_number] += attempt.score


class BestAttemptColumnAggregator(_ResultMixin, Aggregator):
    def __init__(self, problem_count):
        self.result = [None] * problem_count

    def update(self, attempt):
        if self.check(attempt, self.result[attempt.problem_number]):
            self.result[attempt.problem_number] = attempt

    @abc.abstractmethod
    def check(self, candidate, best):
        pass


class FirstSubmittedColumnAggregator(BestAttemptColumnAggregator):
    @staticmethod
    def check(candidate, best):
        return best is None or candidate.time < best.time


class LastSubmittedColumnAggregator(BestAttemptColumnAggregator):
    @staticmethod
    def check(candidate, best):
        return best is None or candidate.time > best.time


class FirstAcceptedColumnAggregator(FirstSubmittedColumnAggregator):
    @classmethod
    def check(cls, candidate, best):
        return candidate.accepted and super().check(candidate, best)


class LastAcceptedColumnAggregator(LastSubmittedColumnAggregator):
    @classmethod
    def check(cls, candidate, best):
        return candidate.accepted and super().check(candidate, best)
