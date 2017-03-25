import contextlib
import re

from ajax_select       import register, LookupChannel
from django.db.models  import Q
from django.utils.html import escape

from . import models


@register('problems')
class ProblemLookup(LookupChannel):
    model = models.Problem

    def get_query(self, q, request):
        query = Q(name__icontains=q) | Q(path__icontains=q)
        with contextlib.suppress(ValueError):
            query |= Q(id=int(q))
        return (
            self.model
            .objects
            .filter(query)
            .order_by('-id')
            .only('id', 'name')
        )[:50]

    def format_match(self, problem):
        return escape(problem)

    format_item_display = format_match


@register('contests')
class ContestLookup(LookupChannel):
    model = models.Contest

    def get_query(self, q, request):
        query = Q(name__icontains=q)
        with contextlib.suppress(ValueError):
            query |= Q(id=int(q))
        return (
            self.model
            .objects
            .filter(query)
            .order_by('-id')
            .only('id', 'name')
        )[:50]

    def format_match(self, contest):
        return escape(contest)

    format_item_display = format_match


@register('problems_in_contests')
class ProblemInContestLookup(LookupChannel):
    model = models.ProblemInContest
    min_length = 5

    regex = re.compile(r'^\s*(.*?)\s*(?:[#№]\s*(.*?)\s*)?$')

    def get_query(self, q, request):
        contest, problem = self.regex.match(q).groups()

        # By contest name.
        query = Q(contest__name__icontains=contest)
        # By contest id.
        with contextlib.suppress(ValueError):
            query |= Q(contest__id=int(contest))

        if problem:
            # By problem name and path.
            problem_query = Q(problem__name__icontains=problem)
            problem_query |= Q(problem__path__icontains=problem)

            try:
                number = int(problem)
            except ValueError:
                # By problem letter.
                if len(problem) == 1 and problem.isalpha():
                    # ord('A') - 1 == 64
                    number = ord(problem.upper()) - 64
                    if 1 <= number <= 26:
                        problem_query |= Q(number=number)
            else:
                # By problem number.
                problem_query |= Q(number=number)
                # By problem id.
                problem_query |= Q(problem__id=number)

            query &= problem_query

        return (
            self.model
            .objects
            .select_related('problem', 'contest')
            .filter(query)
            .order_by('-contest__id', 'number')
            .only('id', 'problem', 'contest', 'number')
        )[:100]

    def format_match(self, problem_in_contest):
        return escape('{0.contest}: {0.number}. {0.problem}'.format(problem_in_contest))

    format_item_display = format_match
