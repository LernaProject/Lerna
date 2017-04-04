from ..aggregators import LastAcceptedAggregator, LastSubmittedAggregator


class LastAttemptsMixin:
    def get_other_aggregators(self):
        return [
            ('last_accepted',  LastAcceptedAggregator()),
            ('last_submitted', LastSubmittedAggregator()),
        ]

    def postprocess_other_aggregations(self, odict):
        for key in ('last_accepted', 'last_submitted'):
            attempt = odict[key]
            if attempt is not None:
                odict[key] = attempt.describe(self.usernames, self.pics)
